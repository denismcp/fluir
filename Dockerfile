# Usa uma imagem oficial do Python estável e leve
FROM python:3.12-slim

# Impede o Python de gerar arquivos .pyc e garante que os logs saiam em tempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala dependências do sistema necessárias para o PostgreSQL e bibliotecas gráficas
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala as dependências do Python primeiro (para aproveitar o cache do Docker)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do seu código para dentro do container
COPY . /app/

# Expõe a porta 8000 (padrão do Django/Gunicorn)
EXPOSE 8000

# Comando para iniciar a aplicação usando Gunicorn (servidor de produção)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "tc_config.wsgi:application"]