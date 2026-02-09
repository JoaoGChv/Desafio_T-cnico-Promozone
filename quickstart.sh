#!/bin/bash
# 🚀 QUICK START - Promozone Collector

echo "╔═══════════════════════════════════════════════════════╗"
echo "║         🚀 PROMOZONE COLLECTOR - QUICK START          ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções
print_step() {
    echo -e "${BLUE}→${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Menu
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Escolha uma opção:${NC}"
    echo ""
    echo "  1) Setup local (primeiro uso)"
    echo "  2) Executar localmente (python -m app.main)"
    echo "  3) Testar endpoints (curl)"
    echo "  4) Rodar unit tests"
    echo "  5) Deploy Cloud Run"
    echo "  6) Validar implementação"
    echo ""
    read -p "Opção (1-6): " choice
else
    choice=$1
fi

case $choice in
    1)
        echo ""
        print_step "Setup Local - Promozone Collector"
        echo ""
        
        # 1. Python version
        print_step "Verificando Python..."
        if command -v python3 &> /dev/null; then
            PYTHON_VERSION=$(python3 --version)
            print_success "$PYTHON_VERSION"
        else
            print_warning "Python 3 não encontrado!"
            exit 1
        fi
        
        # 2. Virtual environment
        print_step "Criando virtual environment..."
        if [ ! -d "venv" ]; then
            python3 -m venv venv
            print_success "Virtual environment criado"
        else
            print_success "Virtual environment já existe"
        fi
        
        # 3. Ativar venv
        print_step "Ativando virtual environment..."
        source venv/bin/activate
        print_success "Virtual environment ativado"
        
        # 4. Instalar dependências
        print_step "Instalando dependências..."
        pip install --upgrade pip > /dev/null 2>&1
        pip install -r requirements.txt > /dev/null 2>&1
        pip install gunicorn pytest pytest-asyncio > /dev/null 2>&1
        print_success "Dependências instaladas"
        
        # 5. .env
        if [ ! -f ".env" ]; then
            print_step "Criando .env..."
            cp .env.example .env
            print_warning "Atualize .env com suas credenciais GCP"
        fi
        
        echo ""
        print_success "Setup concluído!"
        echo ""
        echo "📝 Próximos passos:"
        echo "  1. Configure: export GOOGLE_APPLICATION_CREDENTIALS=/caminho/key.json"
        echo "  2. Atualize: .env com seu GCP_PROJECT_ID"
        echo "  3. Crie tabelas: python infra/create_tables.py seu-projeto"
        echo "  4. Inicie: python -m app.main"
        echo ""
        ;;
    
    2)
        echo ""
        print_step "Iniciando aplicação..."
        
        if [ ! -d "venv" ]; then
            print_warning "Virtual environment não encontrado. Execute: bash quickstart.sh 1"
            exit 1
        fi
        
        source venv/bin/activate
        
        echo ""
        print_success "Aplicação iniciada em http://localhost:8080"
        print_warning "Pressione Ctrl+C para parar"
        echo ""
        
        python -m app.main
        ;;
    
    3)
        echo ""
        print_step "Testando endpoints..."
        echo ""
        
        API_URL="http://localhost:8080"
        
        # Health check
        print_step "GET /health"
        curl -s "$API_URL/health" | python -m json.tool || echo "❌ Erro ao conectar"
        echo ""
        
        # Stats
        print_step "GET /stats"
        curl -s "$API_URL/stats" | python -m json.tool || echo "❌ Erro ao conectar"
        echo ""
        
        echo -e "${YELLOW}Para iniciar coleta, execute:${NC}"
        echo "curl -X POST http://localhost:8080/collect"
        echo ""
        ;;
    
    4)
        echo ""
        print_step "Executando testes..."
        
        if [ ! -d "venv" ]; then
            print_warning "Virtual environment não encontrado. Execute: bash quickstart.sh 1"
            exit 1
        fi
        
        source venv/bin/activate
        
        echo ""
        python -m pytest tests/ -v
        ;;
    
    5)
        echo ""
        print_step "Deploy Cloud Run"
        
        if [ -z "$GCP_PROJECT_ID" ]; then
            read -p "Digite seu GCP_PROJECT_ID: " GCP_PROJECT_ID
        fi
        
        print_step "Project ID: $GCP_PROJECT_ID"
        
        if [ -z "$GCP_PROJECT_ID" ]; then
            print_warning "GCP_PROJECT_ID não configurado"
            exit 1
        fi
        
        echo ""
        print_step "Executando deploy..."
        bash infra/deploy.sh "$GCP_PROJECT_ID"
        ;;
    
    6)
        echo ""
        print_step "Validando implementação..."
        bash validate.sh
        ;;
    
    *)
        echo "Opção inválida"
        exit 1
        ;;
esac

echo ""
