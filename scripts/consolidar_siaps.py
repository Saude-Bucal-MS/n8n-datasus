import csv
import os
import sys
import pymysql

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

COLUNAS_MANTER = {
    "competencia_codigo",
    "municipio_ibge",
    "municipio_nome",
    "cnes",
    "unidade",
    "equipe_codigo",
    "equipe_nome",
    "indicador_codigo",
    "score",
    "numerador",
    "denominador",
    "classificacao",
}

INDICADOR_PARA_TABELA = {
    "111": "siaps_producao_b1",
    "115": "siaps_producao_b2",
    "114": "siaps_producao_b3",
    "112": "siaps_producao_b4",
    "113": "siaps_producao_b5",
    "116": "siaps_producao_b6",
}

INSERT_SQL = """
    INSERT IGNORE INTO {tabela}
        (competencia_codigo, municipio_ibge, municipio_nome, cnes, unidade,
         equipe_codigo, equipe_nome, indicador_codigo, score, numerador,
         denominador, classificacao)
    VALUES
        (%(competencia_codigo)s, %(municipio_ibge)s, %(municipio_nome)s,
         %(cnes)s, %(unidade)s, %(equipe_codigo)s, %(equipe_nome)s,
         %(indicador_codigo)s, %(score)s, %(numerador)s,
         %(denominador)s, %(classificacao)s)
"""


def processar_csv(caminho_csv):
    nome_arquivo = os.path.basename(caminho_csv)

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cur = conn.cursor()
    except Exception as e:
        print(f"Erro ao conectar no MySQL: {e}")
        return

    try:
        # Verifica se já foi processado
        cur.execute(
            "SELECT nome_arquivo FROM siaps_log_processamento_arquivos WHERE nome_arquivo = %s",
            (nome_arquivo,)
        )
        if cur.fetchone():
            print(f"[IGNORADO] {nome_arquivo} já foi processado anteriormente.")
            return

        print(f"-> Iniciando: {nome_arquivo}")

        # Lê o CSV e agrupa por tabela de destino
        lotes = {tabela: [] for tabela in set(INDICADOR_PARA_TABELA.values())}

        with open(caminho_csv, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            for linha in reader:
                filtrada = {k: v for k, v in linha.items() if k in COLUNAS_MANTER}
                codigo = filtrada.get("indicador_codigo", "").strip()
                tabela = INDICADOR_PARA_TABELA.get(codigo)

                if tabela is None:
                    print(f"   [AVISO] Código de indicador desconhecido: {codigo}")
                    continue

                lotes[tabela].append(filtrada)

        # Insere cada lote na tabela correspondente
        for tabela, registros in lotes.items():
            if not registros:
                continue
            cur.executemany(INSERT_SQL.format(tabela=tabela), registros)
            print(f"   [OK] {tabela}: {cur.rowcount} registros inseridos.")

        # Registra no log
        cur.execute(
            "INSERT INTO siaps_log_processamento_arquivos (nome_arquivo) VALUES (%s)",
            (nome_arquivo,)
        )

        conn.commit()
        print(f"   [OK] {nome_arquivo} processado e gravado.")

    except Exception as e:
        conn.rollback()
        print(f"   [ERRO] Falha em {nome_arquivo}: {e}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python consolidar_siaps.py <caminho_do_csv>")
        exit(1)

    processar_csv(sys.argv[1])
