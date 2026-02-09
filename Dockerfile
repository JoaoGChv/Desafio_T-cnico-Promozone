# Use a imagem base slim do Python 3.11
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY app/ app/

# Expõe porta
EXPOSE 8080

# Define variáveis de ambiente
ENV FLASK_APP=app.main:create_app
ENV PORT=8080

# Comando de inicialização
CMD exec gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 --access-logfile - --error-logfile - "app.main:create_app()"
