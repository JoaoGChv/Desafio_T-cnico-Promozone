#!/bin/bash
# Script para setup local da aplicação

echo "🚀 Setup Local do Promozone Collector"
echo "====================================="

# 1. Criar virtual environment
echo "📦 Criando virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependências
echo "📥 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn python-dotenv

# 3. Criar .env local
echo "⚙️  Criando arquivo .env local..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Arquivo .env criado. Atualize com suas credenciais GCP!"
fi

# 4. Setup BigQuery local (opcional)
echo ""
echo "💡 Próximos passos:"
echo ""
echo "1. Configure suas credenciais GCP:"
echo "   export GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/seu/key.json"
echo ""
echo "2. Atualize o arquivo .env com seu PROJECT_ID"
echo ""
echo "3. Crie as tabelas no BigQuery:"
echo "   python infra/create_tables.py seu-projeto-gcp"
echo ""
echo "4. Execute a aplicação:"
echo "   python -m app.main"
echo ""
echo "✅ Setup concluído!"
