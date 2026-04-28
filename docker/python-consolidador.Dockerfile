
FROM python:3.10-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala as dependências de sistema necessárias para compilar algumas libs de banco se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instala as bibliotecas Python que seu script exige
# Pymysql para o banco e Cryptography para a segurança do MySQL 8.0
RUN pip install --no-cache-dir pymysql cryptography

# O container apenas aguarda o comando do n8n para executar
# Mapearemos o script via volumes no docker-compose para facilitar atualizações
COPY scripts/consolidar_odonto.py /app/consolidar_odonto.py

CMD ["python", "/app/consolidar_odonto.py"]