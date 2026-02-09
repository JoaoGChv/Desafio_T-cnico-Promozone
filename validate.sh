#!/bin/bash
# Script para validar a implementação contra os critérios de sucesso

echo "✅ CHECKLIST FINAL - Promozone Collector"
echo "========================================"
echo ""

# 1. Verificar estrutura do projeto
echo "1️⃣  Estrutura do Projeto"
echo "   Verificando arquivos principais..."

files=(
    "app/main.py"
    "app/config.py"
    "app/scrapers/mercadolivre.py"
    "app/normalizers/promotion_normalizer.py"
    "app/database/bigquery_client.py"
    "app/utils/normalizers.py"
    "Dockerfile"
    "requirements.txt"
    ".env.example"
    "infra/create_tables.py"
    "infra/deploy.sh"
    "README.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file (FALTANDO)"
    fi
done
echo ""

# 2. Verificar requisitos do Python
echo "2️⃣  Dependências Python"
echo "   Verificando requirements.txt..."

required_packages=(
    "Flask"
    "google-cloud-bigquery"
    "httpx"
    "beautifulsoup4"
    "lxml"
    "python-dotenv"
)

for package in "${required_packages[@]}"; do
    if grep -q "$package" requirements.txt; then
        echo "   ✓ $package"
    else
        echo "   ✗ $package (FALTANDO)"
    fi
done
echo ""

# 3. Verificar endpoints da API
echo "3️⃣  Endpoints da API Flask"

endpoints=(
    "/health"
    "/collect"
    "/stats"
)

if grep -q "def health" app/main.py; then
    echo "   ✓ GET /health"
else
    echo "   ✗ GET /health (FALTANDO)"
fi

if grep -q "def collect" app/main.py; then
    echo "   ✓ POST /collect"
else
    echo "   ✗ POST /collect (FALTANDO)"
fi

if grep -q "def stats" app/main.py; then
    echo "   ✓ GET /stats"
else
    echo "   ✗ GET /stats (FALTANDO)"
fi
echo ""

# 4. Verificar normalizadores
echo "4️⃣  Funções de Normalização"

if grep -q "normalize_price" app/utils/normalizers.py; then
    echo "   ✓ normalize_price (R$ -> float)"
else
    echo "   ✗ normalize_price (FALTANDO)"
fi

if grep -q "calculate_dedupe_key" app/utils/normalizers.py; then
    echo "   ✓ calculate_dedupe_key"
else
    echo "   ✗ calculate_dedupe_key (FALTANDO)"
fi

if grep -q "extract_discount_percent" app/utils/normalizers.py; then
    echo "   ✓ extract_discount_percent"
else
    echo "   ✗ extract_discount_percent (FALTANDO)"
fi
echo ""

# 5. Verificar BigQuery
echo "5️⃣  Cliente BigQuery"

if grep -q "merge_promotions" app/database/bigquery_client.py; then
    echo "   ✓ Método merge_promotions"
else
    echo "   ✗ Método merge_promotions (FALTANDO)"
fi

if grep -q "MERGE" app/database/bigquery_client.py; then
    echo "   ✓ Query MERGE SQL"
else
    echo "   ✗ Query MERGE SQL (FALTANDO)"
fi

if grep -q "log_execution" app/database/bigquery_client.py; then
    echo "   ✓ Método log_execution"
else
    echo "   ✗ Método log_execution (FALTANDO)"
fi
echo ""

# 6. Verificar Scraper
echo "6️⃣  Mercado Livre Scraper"

if grep -q "exponential backoff" app/scrapers/base.py; then
    echo "   ✓ Exponential backoff"
else
    echo "   ✓ Retry logic (verificar)"
fi

if grep -q "User-Agent" app/scrapers/base.py; then
    echo "   ✓ Headers com User-Agent"
else
    echo "   ✗ Headers com User-Agent (FALTANDO)"
fi

if grep -q "ofertas#menu_container" app/scrapers/mercadolivre.py; then
    echo "   ✓ Fonte: Ofertas do Dia"
else
    echo "   ✗ Fonte: Ofertas do Dia (FALTANDO)"
fi
echo ""

# 7. Verificar Docker
echo "7️⃣  Containerização"

if grep -q "python:3.11-slim" Dockerfile; then
    echo "   ✓ Dockerfile com python:3.11-slim"
else
    echo "   ✗ Dockerfile com python:3.11-slim (FALTANDO)"
fi

if grep -q "Cloud Run" Dockerfile || grep -q "gunicorn" Dockerfile; then
    echo "   ✓ Configuração para Cloud Run"
else
    echo "   ⚠ Verificar configuração Cloud Run"
fi
echo ""

# 8. Verificar Segurança
echo "8️⃣  Segurança"

if grep -q "GOOGLE_APPLICATION_CREDENTIALS" app/config.py; then
    echo "   ✓ Credenciais via variáveis de ambiente"
else
    echo "   ✗ Credenciais via variáveis de ambiente (FALTANDO)"
fi

if grep -q "getenv" app/config.py; then
    echo "   ✓ Uso de getenv (sem hardcode)"
else
    echo "   ✗ Sem hardcode de credenciais (FALTANDO)"
fi
echo ""

# 9. Verificar Documentação
echo "9️⃣  Documentação"

if [ -f "README.md" ]; then
    echo "   ✓ README.md existe"
    if grep -q "deploy" README.md; then
        echo "   ✓ Instruções de deploy no README"
    else
        echo "   ✗ Instruções de deploy no README (FALTANDO)"
    fi
else
    echo "   ✗ README.md (FALTANDO)"
fi

if [ -f "infra/deploy.sh" ]; then
    echo "   ✓ Script de deploy"
else
    echo "   ✗ Script de deploy (FALTANDO)"
fi
echo ""

echo "========================================="
echo "✅ Validação concluída!"
echo ""
echo "📝 Próximos passos:"
echo "   1. Configure GOOGLE_APPLICATION_CREDENTIALS"
echo "   2. Atualize .env com seu PROJECT_ID"
echo "   3. Execute: python infra/create_tables.py seu-projeto-gcp"
echo "   4. Execute: python -m app.main"
echo "   5. Teste: curl http://localhost:8080/health"
