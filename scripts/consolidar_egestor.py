"""
consolidar_egestor.py

Consolida pagamento do e-Gestor APS (uma competência/parcela, todos os
municípios de MS) em e_gestor_pagamento_esb, e registra o arquivo em
e_gestor_log_processamento_arquivos.

Dois modos de uso:

1) Modo arquivo (usado pelo n8n, que já buscou e salvou o JSON em disco):
    python consolidar_egestor.py /caminho/para/egestor_202609.json

2) Modo parcela (busca direto na API, para rodar local/backfill sem n8n):
    python consolidar_egestor.py --parcela 202501
    python consolidar_egestor.py --parcela 202501 --dir dados/egestor_pagamento

No modo --parcela, o script baixa da API, salva em disco com o mesmo nome
que o n8n usaria (egestor_<parcela>.json) e em seguida consolida normalmente.
Isso faz com que, mais tarde, o n8n reconheça a parcela como já processada
(via e_gestor_log_processamento_arquivos) e não a baixe de novo.

Variáveis de ambiente esperadas:
    DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pymysql

API_URL = "https://relatorioaps-prd.saude.gov.br/financiamento/pagamento"
CO_UF_MS = 50

CAMPOS_ESB = {
    "qtTetoSb40h": "qt_teto_esb_40h",
    "qtTetoSbChDif": "qt_teto_esb_ch_dif",
    "qtSb40hCredenciada": "qt_esb_40h_credenciada",
    "qtSb40hDifCredenciada": "qt_esb_ch_dif_credenciada",
    "qtSb40hHomologado": "qt_esb_40h_homologada",
    "qtSbChDifHomologado": "qt_esb_ch_dif_homologada",
    "qtSbPagamentoModalidadeI": "qt_esb_modalidade_i_pagas",
    "qtSbPagamentoModalidadeII": "qt_esb_modalidade_ii_pagas",
    "qtSbPagamentoDifModalidade20Horas": "qt_esb_ch_dif_20h_pagas",
    "qtSbPagamentoDifModalidade30Horas": "qt_esb_ch_dif_30h_pagas",
    "qtSbEqpQuilombAssentModalI": "qt_esb_quilomb_assent_modal_i",
    "qtSbEqpQuilombAssentModalII": "qt_esb_quilomb_assent_modal_ii",
    "qtSbEquipeImplantacao": "qt_esb_implantacao",
    "vlPagamentoEsb40h": "vl_custeio_esb_40h",
    "vlPagamentoEsbChDiferenciada": "vl_custeio_esb_ch_dif",
    "vlPagamentoImplantacaoEsb40h": "vl_implantacao_esb_40h",
    "vlPagamentoEsb40hQualidade": "vl_qualidade_esb_40h",
    "vlPagamentoEsbChDifQualidade": "vl_qualidade_esb_ch_dif",
    "vlPagamentoQualidadeExtraEsb40H": "vl_parcela_adicional_qualidade",
}

COLUNAS_TABELA = ["parcela_codigo", "competencia_codigo", "municipio_ibge"] + list(
    CAMPOS_ESB.values()
)

SQL_INSERT = f"""
    INSERT INTO e_gestor_pagamento_esb ({", ".join(COLUNAS_TABELA)})
    VALUES ({", ".join(["%s"] * len(COLUNAS_TABELA))})
    ON DUPLICATE KEY UPDATE
        {", ".join(f"{col} = VALUES({col})" for col in COLUNAS_TABELA if col not in ("parcela_codigo", "municipio_ibge"))}
"""

SQL_REGISTRAR_LOG = """
    INSERT INTO e_gestor_log_processamento_arquivos (nome_arquivo)
    VALUES (%s)
    ON DUPLICATE KEY UPDATE data_processamento = CURRENT_TIMESTAMP
"""


def montar_config_db() -> dict:
    return {
        "host": os.environ["DB_HOST"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "database": os.environ["DB_NAME"],
        "charset": "utf8mb4",
    }


def extrair_linha(municipio_ibge: str, comp_cnes: str, parcela: str, item: dict) -> tuple:
    valores = [parcela, comp_cnes, municipio_ibge]
    for campo_json in CAMPOS_ESB:
        valores.append(item.get(campo_json, 0) or 0)
    return tuple(valores)


def validar_parcela(parcela: str) -> None:
    if not re.fullmatch(r"\d{6}", parcela):
        print(f"[erro] parcela inválida: {parcela!r} (esperado formato AAAAMM, ex.: 202501)")
        sys.exit(1)


def buscar_e_salvar(parcela: str, diretorio: Path) -> Path:
    """Busca a parcela na API do e-Gestor e salva em disco, igual ao que o n8n faria."""
    validar_parcela(parcela)
    diretorio.mkdir(parents=True, exist_ok=True)
    destino = diretorio / f"egestor_{parcela}.json"

    params = {
        "unidadeGeografica": "MUNICIPIO",
        "coUf": CO_UF_MS,
        "nuParcelaInicio": parcela,
        "nuParcelaFim": parcela,
        "tipoRelatorio": "COMPLETO",
    }
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"

    print(f"Buscando parcela {parcela} na API do e-Gestor...")
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            conteudo = resp.read()
    except Exception as e:
        print(f"[erro] falha ao buscar {parcela} na API: {e}")
        sys.exit(1)

    destino.write_bytes(conteudo)
    print(f"Salvo em {destino}")
    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "arquivo",
        nargs="?",
        default=None,
        help="Caminho de um JSON já baixado (modo usado pelo n8n)",
    )
    parser.add_argument(
        "--parcela",
        default=None,
        help="Parcela no formato AAAAMM a buscar direto na API (modo local/backfill)",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("dados/egestor_pagamento"),
        help="Diretório onde salvar o JSON quando usar --parcela (padrão: dados/egestor_pagamento)",
    )
    args = parser.parse_args()

    if args.arquivo and args.parcela:
        print("[erro] use ou um caminho de arquivo, ou --parcela, não os dois")
        sys.exit(1)

    if args.parcela:
        caminho = buscar_e_salvar(args.parcela, args.dir)
    elif args.arquivo:
        caminho = Path(args.arquivo)
    else:
        parser.print_help()
        sys.exit(1)

    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        sys.exit(1)

    dados = json.loads(caminho.read_text(encoding="utf-8"))
    pagamentos = dados.get("pagamentos", [])

    linhas = []
    for item in pagamentos:
        municipio_ibge = item.get("coMunicipioIbge")
        comp_cnes = item.get("nuCompCnes")
        parcela = item.get("nuParcela")
        if not municipio_ibge or not parcela:
            print(f"[aviso] item sem municipio/parcela, pulando: {item}")
            continue
        linhas.append(extrair_linha(municipio_ibge, comp_cnes, parcela, item))

    if not linhas:
        print(f"[erro] {caminho.name} não trouxe nenhuma linha válida, nada será inserido")
        sys.exit(1)

    try:
        conn = pymysql.connect(**montar_config_db())
    except pymysql.Error as e:
        print(f"Falha ao conectar no MySQL: {e}")
        sys.exit(1)

    cursor = conn.cursor()
    try:
        cursor.executemany(SQL_INSERT, linhas)
        cursor.execute(SQL_REGISTRAR_LOG, (caminho.name,))
        conn.commit()
        print(f"{caminho.name}: {len(linhas)} linhas consolidadas em e_gestor_pagamento_esb")
    except pymysql.Error as e:
        conn.rollback()
        print(f"Erro durante a consolidação, rollback aplicado: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()