import sqlite3
import pymysql
import glob
import os
import sys
from collections import defaultdict

# Os valores reais devem residir apenas no seu arquivo .env
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'indicadores_sus'),
    'autocommit': False,
    'connect_timeout': 10
}

# Validação Obrigatória: Impede a execução se as credenciais não forem injetadas
if not DB_CONFIG['password'] or not DB_CONFIG['user']:
    print("\n[ERRO DE SEGURANÇA] As variáveis DB_USER ou DB_PASSWORD não foram definidas.")
    print("Certifique-se de que o arquivo .env está configurado ou as variáveis foram passadas ao container.\n")
    exit(1)

# Caminhos de dados
PASTA_PAMS = r"/data"
PASTA_POP = r"/data"

CBO_CD = ('223208', '223293', '223272')
CBO_TODOS = ('223208', '223293', '223272', '322405', '322425', '322415', '322430')

PROC_CLINICOS_IND3 = (
    '0101020058', '0101020066', '0101020074', '0101020082', '0101020090',
    '0307010015', '0307010031', '0307010066', '0307010074', '0307010082',
    '0307010104', '0307010112', '0307010120', '0307010139', '0307020010',
    '0307020029', '0307020070', '0307030024', '0307030040', '0307030059',
    '0307030067', '0307030075', '0307030083', '0414020138', '0414020146'
)
PROC_PREVENTIVOS_IND5 = ('0101020058', '0101020066', '0101020074', '0101020082', '0101020090', '0101020104')
PROC_RESTAURADORES_IND6 = ('0307010031', '0307010082', '0307010090', '0307010104', '0307010112', '0307010120', '0307010139', '0307010074')

def extrair_dados_pams(cur_sqlite, tabela):
    consolidado = defaultdict(lambda: [0]*9)
    queries = [
        (0, f"SELECT PA_UFMUN, SUM(PA_QTDAPR) FROM {tabela} WHERE PA_PROC_ID = '0301010153' AND PA_DOCORIG = 'I' AND PA_CBOCOD IN {CBO_CD} AND PA_UFMUN LIKE '50%%' GROUP BY PA_UFMUN"),
        (1, f"SELECT PA_UFMUN, SUM(PA_QTDAPR) FROM {tabela} WHERE PA_PROC_ID = '0301010072' AND PA_DOCORIG = 'I' AND PA_CBOCOD IN {CBO_CD} AND PA_UFMUN LIKE '50%%' GROUP BY PA_UFMUN"),
        (2, f"SELECT PA_UFMUN, SUM(PA_QTDAPR) FROM {tabela} WHERE PA_PROC_ID IN ('0414020138', '0414020120', '0414020146') AND PA_DOCORIG = 'I' AND PA_CBOCOD IN {CBO_CD} AND PA_UFMUN LIKE '50%%' GROUP BY PA_UFMUN"),
        (3, f"SELECT PA_UFMUN, SUM(PA_QTDAPR) FROM {tabela} WHERE PA_PROC_ID IN {PROC_CLINICOS_IND3} AND PA_DOCORIG = 'I' AND PA_CBOCOD IN {CBO_CD} AND PA_UFMUN LIKE '50%%' GROUP BY PA_UFMUN"),
        (4, f"SELECT PA_UFMUN, SUM(PA_QTDAPR) FROM {tabela} WHERE PA_PROC_ID = '0101020031' AND PA_IDADE BETWEEN 6 AND 12 AND PA_CBOCOD IN {CBO_TODOS} AND PA_UFMUN LIKE '50%%' GROUP BY PA_UFMUN"),
        (5, f"SELECT PA_UFMUN, SUM(PA_QTDAPR) FROM {tabela} WHERE PA_PROC_ID IN {PROC_PREVENTIVOS_IND5} AND PA_DOCORIG = 'I' AND PA_CBOCOD IN {CBO_TODOS[:5]} AND PA_UFMUN LIKE '50%%' GROUP BY PA_UFMUN"),
        (6, f"SELECT PA_UFMUN, SUM(PA_QTDAPR) FROM {tabela} WHERE PA_DOCORIG = 'I' AND PA_CBOCOD IN {CBO_TODOS[:5]} AND PA_UFMUN LIKE '50%%' GROUP BY PA_UFMUN"),
        (7, f"SELECT PA_UFMUN, SUM(PA_QTDAPR) FROM {tabela} WHERE PA_PROC_ID = '0307010074' AND PA_DOCORIG = 'I' AND PA_CBOCOD IN {CBO_CD} AND PA_UFMUN LIKE '50%%' GROUP BY PA_UFMUN"),
        (8, f"SELECT PA_UFMUN, SUM(PA_QTDAPR) FROM {tabela} WHERE PA_PROC_ID IN {PROC_RESTAURADORES_IND6} AND PA_DOCORIG = 'I' AND PA_CBOCOD IN {CBO_CD} AND PA_UFMUN LIKE '50%%' GROUP BY PA_UFMUN")
    ]
    for col_idx, sql in queries:
        cur_sqlite.execute(sql)
        for mun, val in cur_sqlite.fetchall():
            consolidado[mun][col_idx] = val or 0
    return consolidado


def processar_arquivos(pattern=None):
    try:
        conn_mysql = pymysql.connect(**DB_CONFIG)
        cur_mysql = conn_mysql.cursor()
    except Exception as e:
        print(f"Erro ao conectar no MySQL: {e}")
        return

    try:
        cur_mysql.execute("SELECT nome_arquivo FROM log_processamento_arquivos")
        processados = {row[0] for row in cur_mysql.fetchall()}
    except pymysql.err.ProgrammingError:
        print("Tabelas não encontradas no MySQL. Execute o script SQL de criação primeiro.")
        return

    cur_mysql.execute("SELECT codigo_ibge FROM municipios_ms")
    mun_validos = {str(row[0]) for row in cur_mysql.fetchall()}

    arquivos = glob.glob(os.path.join(PASTA_PAMS, "*.sqlite")) + \
               glob.glob(os.path.join(PASTA_POP, "*.sqlite"))

    # Filtra pelo pattern recebido do n8n, se informado
    if pattern:
        arquivos = [a for a in arquivos if pattern in os.path.basename(a)]

    for caminho in arquivos:
        nome = os.path.basename(caminho)
        if nome in processados:
            continue

        print(f"-> Iniciando: {nome}")
        try:
            conn_sqlite = sqlite3.connect(caminho)
            cur_sqlite = conn_sqlite.cursor()

            tabela = cur_sqlite.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchone()[0]

            if nome.startswith("PAMS"):
                base = os.path.splitext(nome)[0]
                data_comp = f"20{base[4:6]}-{base[6:8]}-01"
                dados = extrair_dados_pams(cur_sqlite, tabela)
                lista_v = [
                    (data_comp, mun, v[0], v[1], v[0], v[2], v[3], v[4], v[5], v[6], v[7], v[8])
                    for mun, v in dados.items()
                ]
                sql_pams = """
                    INSERT INTO producao_odonto_consolidada
                    (data, municipio, ind01_num_prim_consulta, ind02_num_trat_concluido,
                     ind02_den_prim_consulta, ind03_num_exodontias, ind03_den_total_clinicos,
                     ind04_num_escovacao_6_12, ind05_num_preventivos, ind05_den_total_individuais,
                     ind06_num_tra_art, ind06_den_restauradores)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cur_mysql.executemany(sql_pams, lista_v)

            elif nome.startswith("POPSBR"):
                base = os.path.splitext(nome)[0]
                ano = "20" + base[6:8]
                cur_sqlite.execute(f"SELECT COD_MUN, SUM(POP) FROM {tabela} WHERE COD_MUN LIKE '50%' GROUP BY COD_MUN")
                pops = {str(k): v for k, v in cur_sqlite.fetchall()}
                cur_sqlite.execute(f"SELECT COD_MUN, SUM(POP) FROM {tabela} WHERE IDADE BETWEEN 6 AND 12 AND COD_MUN LIKE '50%' GROUP BY COD_MUN")
                pops612 = {str(k): v for k, v in cur_sqlite.fetchall()}

                lista_pop = [
                    (ano, mun, pops.get(mun, 0), pops612.get(mun, 0))
                    for mun in (set(pops.keys()) | set(pops612.keys()))
                    if mun in mun_validos
                ]
                sql_pop = """
                    INSERT INTO populacao_municipios (ano, municipio, populacao_total, populacao_6_12)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        populacao_total=VALUES(populacao_total),
                        populacao_6_12=VALUES(populacao_6_12)
                """
                cur_mysql.executemany(sql_pop, lista_pop)

            cur_mysql.execute("INSERT INTO log_processamento_arquivos (nome_arquivo) VALUES (%s)", (nome,))
            conn_mysql.commit()
            conn_sqlite.close()
            print(f"   [OK] {nome} processado e gravado.")

        except Exception as e:
            conn_mysql.rollback()
            print(f"   [ERRO] Falha em {nome}: {e}")

    cur_mysql.close()
    conn_mysql.close()
    print("\nProcessamento concluído.")


if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else None
    processar_arquivos(pattern)