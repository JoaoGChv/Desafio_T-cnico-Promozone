# Promozone Promotion Collector

Coletor automático de promoções do Mercado Livre com deduplicação inteligente e deploy no GCP Cloud Run.

## 🎯 Visão Geral

**Promozone** é um serviço serverless (Flask + Cloud Run) que:

- ✅ Coleta promoções de 3 fontes do Mercado Livre
- ✅ Normaliza e valida dados em tempo real
- ✅ Realiza deduplicação via MERGE SQL no BigQuery
- ✅ Registra logs operacionais detalhados
- ✅ Fornece API REST para consultas e monitoramento

### Pipeline de Dados

```
API Trigger (/collect)
    ↓
Scraper (httpx + BeautifulSoup4)
    ↓
Normalizer (validação e enriquecimento)
    ↓
BigQuery MERGE (deduplicação automática)
    ↓
Execution Logs (rastreamento completo)
```

---

## 📋 Arquitetura e Stack

### Tecnologias

| Componente | Tecnologia |
|-----------|-----------|
| Framework Web | Flask 3.0 |
| HTTP Client | httpx (async) |
| Parser HTML | BeautifulSoup4 + lxml |
| Database | Google BigQuery |
| Container | Docker (python:3.11-slim) |
| Deploy | Cloud Run (GCP) |
| Logging | JSON estruturado |

### Estrutura do Projeto

```
/Desafio-Promozone
├── app/
│   ├── __init__.py
│   ├── config.py              # Configurações centralizadas
│   ├── main.py                # Aplicação Flask principal
│   ├── scrapers/
│   │   ├── base.py            # Scraper base com retry
│   │   └── mercadolivre.py    # Implementação específica
│   ├── normalizers/
│   │   └── promotion_normalizer.py  # Normalização de dados
│   ├── database/
│   │   └── bigquery_client.py  # Cliente BigQuery com MERGE
│   └── utils/
│       ├── logger.py          # Logging estruturado
│       ├── normalizers.py     # Funções de normalização
│       └── retry.py           # Retry com exponential backoff
├── infra/
│   ├── create_tables.py       # Script para setup BigQuery
│   ├── deploy.sh              # Deploy automático Cloud Run
│   └── setup_local.sh         # Setup local
├── Dockerfile                 # Imagem para Cloud Run
├── requirements.txt           # Dependências Python
├── .env.example              # Template de variáveis
└── README.md                 # Este arquivo
```

---

## 🚀 Quickstart

### 1️⃣ Local Setup

```bash
# Clone ou extraia o projeto
cd Desafio-Promozone

# Setup local
bash infra/setup_local.sh

# Ative o virtual environment
source venv/bin/activate

# Configure credenciais GCP
export GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/key.json

# Atualize .env com seu PROJECT_ID
# GCP_PROJECT_ID=seu-projeto-gcp
```

### 2️⃣ Criar Tabelas no BigQuery

```bash
# Cria dataset e tabelas automaticamente
python infra/create_tables.py seu-projeto-gcp promozone
```

### 3️⃣ Executar Localmente

```bash
# Instale gunicorn para servidor production-like
pip install gunicorn

# Inicie a aplicação
python -m app.main

# Ou com gunicorn
gunicorn --bind 0.0.0.0:8080 --workers 4 "app.main:create_app()"
```

A API estará disponível em `http://localhost:8080`

### 4️⃣ Testar Endpoints

```bash
# Health check
curl http://localhost:8080/health

# Iniciar coleta (POST)
curl -X POST http://localhost:8080/collect

# Ver estatísticas (últimas 24h)
curl http://localhost:8080/stats
```

---

## 🐳 Docker e Cloud Run

### Build Local

```bash
docker build -t promozone-collector .
docker run -p 8080:8080 \
  -e GCP_PROJECT_ID=seu-projeto \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/gcp-key.json \
  -v /caminho/para/key.json:/app/secrets/gcp-key.json:ro \
  promozone-collector
```

### Deploy no Cloud Run

```bash
# Execute o script de deploy
bash infra/deploy.sh seu-projeto-gcp

# Ou manualmente:
gcloud run deploy promozone-collector \
  --image gcr.io/seu-projeto-gcp/promozone-collector:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 2 \
  --timeout 120
```

---

## 📊 Endpoints da API

### `GET /health`

Health check simples.

**Response:**
```json
{
  "status": "healthy"
}
```

---

### `POST /collect`

Inicia ciclo completo de coleta e persistência.

**Response:**
```json
{
  "execution_id": "uuid-da-execução",
  "status": "success",
  "items_collected": 75,
  "items_normalized": 75,
  "items_inserted": 68,
  "items_deduplicated": 7,
  "duration_seconds": 23.45,
  "start_time": "2026-02-09T10:15:30.123456",
  "end_time": "2026-02-09T10:15:53.573456"
}
```

---

### `GET /stats`

Retorna estatísticas das últimas 24 horas.

**Response:**
```json
{
  "executions": 3,
  "total_items": 156,
  "unique_items": 142,
  "by_source": {
    "daily_offers": 52,
    "technology": 48,
    "electronics": 56
  },
  "avg_discount_percent": 18.5
}
```

---

## 🔐 Segurança e Variáveis de Ambiente

**NUNCA** faça hardcode de credenciais. Use variáveis de ambiente:

```bash
export GCP_PROJECT_ID=seu-projeto
export GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/key.json
export BIGQUERY_DATASET=promozone
export REQUEST_TIMEOUT=30
export MAX_RETRIES=3
```

Para Cloud Run, use **Secret Manager**:

```bash
gcloud secrets create gcp-key --data-file=/caminho/para/key.json

gcloud run deploy promozone-collector \
  --update-secrets GOOGLE_APPLICATION_CREDENTIALS=gcp-key:latest
```

---

## 📈 Schema BigQuery

### Tabela: `promotions`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `marketplace` | STRING | Nome do marketplace (ex: "mercadolivre") |
| `item_id` | STRING | ID único do produto (ex: "MLB123456789") |
| `url` | STRING | URL do produto |
| `title` | STRING | Título/nome do produto |
| `price` | NUMERIC | Preço atual em BRL |
| `original_price` | NUMERIC | Preço original (nullable) |
| `discount_percent` | FLOAT64 | Percentual de desconto (nullable) |
| `seller` | STRING | Nome do vendedor |
| `image_url` | STRING | URL da imagem do produto |
| `source` | STRING | Fonte da coleta (daily_offers, technology, electronics) |
| `dedupe_key` | STRING | Chave de deduplicação (marketplace#item_id#price) |
| `execution_id` | STRING | ID da execução que coletou |
| `collected_at` | TIMESTAMP | Momento da coleta |
| `inserted_at` | TIMESTAMP | Momento da inserção no BigQuery |

**Índices de Clustering:** `dedupe_key`, `execution_id`

---

### Tabela: `execution_logs`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `execution_id` | STRING | ID único da execução |
| `start_time` | TIMESTAMP | Hora de início |
| `end_time` | TIMESTAMP | Hora de término |
| `items_collected` | INTEGER | Total de itens coletados |
| `items_inserted` | INTEGER | Total de itens inseridos (novos) |
| `items_deduplicated` | INTEGER | Total de itens duplicados |
| `status` | STRING | Status (success/error) |
| `error_message` | STRING | Mensagem de erro se houver (nullable) |

---

## 🔍 Queries SQL Úteis

### Últimas Coletas (últimas 24h)

```sql
SELECT
  execution_id,
  start_time,
  end_time,
  items_collected,
  items_inserted,
  items_deduplicated,
  status
FROM `seu-projeto.promozone.execution_logs`
WHERE start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
ORDER BY start_time DESC
LIMIT 10;
```

### Produtos Mais Descontados

```sql
SELECT
  title,
  seller,
  price,
  original_price,
  discount_percent,
  source,
  collected_at
FROM `seu-projeto.promozone.promotions`
WHERE collected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
ORDER BY discount_percent DESC
LIMIT 20;
```

### Produtos Duplicados (últimas 24h)

```sql
SELECT
  dedupe_key,
  COUNT(*) as count,
  ARRAY_AGG(DISTINCT execution_id) as executions
FROM `seu-projeto.promozone.promotions`
WHERE collected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY dedupe_key
HAVING COUNT(*) > 1
ORDER BY count DESC;
```

### Estatísticas por Fonte

```sql
SELECT
  source,
  COUNT(*) as total_items,
  COUNT(DISTINCT item_id) as unique_items,
  AVG(price) as avg_price,
  AVG(discount_percent) as avg_discount,
  MIN(collected_at) as first_collection,
  MAX(collected_at) as last_collection
FROM `seu-projeto.promozone.promotions`
WHERE collected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY source
ORDER BY total_items DESC;
```

---

## 🧪 Testes

### Teste Local sem GCP

```bash
# Instale dependências de teste
pip install pytest pytest-asyncio

# Execute testes
pytest tests/
```

### Teste de Scraping

```bash
python -c "
import asyncio
from app.scrapers.mercadolivre import MercadoLivreScraper

async def test():
    scraper = MercadoLivreScraper()
    results = await scraper.scrape_all()
    for source, items in results.items():
        print(f'{source}: {len(items)} itens')

asyncio.run(test())
"
```

---

## 📝 Checklist de Implementação

- [x] Arquitetura fim-a-fim (Scraper → Normalizer → BigQuery → Logs)
- [x] Scraper com retry e exponential backoff
- [x] Normalização de preços (R$ 1.250,50 → 1250.50)
- [x] MERGE SQL com deduplicação automática
- [x] API Flask com 3 endpoints (/health, /collect, /stats)
- [x] Logging estruturado em JSON
- [x] Dockerfile para Cloud Run
- [x] Variáveis de ambiente (sem hardcode)
- [x] Setup scripts (local e cloud)
- [x] Documentação completa
- [x] Queries SQL de validação

---

## 📚 Referências

- [Google Cloud BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Cloud Run Quickstart](https://cloud.google.com/run/docs/quickstarts/build-and-deploy)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [httpx Async Client](https://www.python-httpx.org/)
- [BeautifulSoup4 Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

---

## 🐛 Troubleshooting

### Erro: "Permission denied" no BigQuery

```bash
# Verifique credenciais GCP
gcloud auth list
gcloud config list

# Redefina credenciais
export GOOGLE_APPLICATION_CREDENTIALS=/caminho/correto/key.json
```

### Scraper não coleta itens

- Verifique os seletores CSS em `app/scrapers/mercadolivre.py`
- O Mercado Livre pode ter alterado a estrutura HTML
- Aumente `REQUEST_TIMEOUT` se o site for lento

### Erro: "Table not found" no BigQuery

```bash
# Recrie as tabelas
python infra/create_tables.py seu-projeto-gcp
```

---

## 📞 Suporte

Para dúvidas ou issues:

1. Verifique os logs estruturados em JSON
2. Execute queries SQL de validação
3. Valide as variáveis de ambiente
4. Teste endpoints localmente com curl

---

**Desenvolvido com ❤️ para o Promozone Challenge (24h Sprint)**
