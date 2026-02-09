# Guia Completo de Deploy - Promozone Collector

## 📋 Pré-requisitos

- ✅ Conta Google Cloud com projeto criado
- ✅ `gcloud` CLI instalada e configurada
- ✅ Docker instalado (para build local)
- ✅ Python 3.11+
- ✅ Arquivo de credenciais GCP (JSON key)

---

## 🔧 Configuração do Projeto GCP

### Passo 1: Criar Projeto no GCP

```bash
export GCP_PROJECT_ID=seu-projeto-promozone

# Crie um novo projeto
gcloud projects create $GCP_PROJECT_ID --name="Promozone Collector"

# Configure como projeto padrão
gcloud config set project $GCP_PROJECT_ID
```

### Passo 2: Habilitar APIs Necessárias

```bash
gcloud services enable \
  bigquery.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com
```

### Passo 3: Criar Service Account e Chaves

```bash
# Crie uma service account
gcloud iam service-accounts create promozone-collector \
  --display-name="Service Account para Promozone Collector"

# Atribua role BigQuery Admin
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:promozone-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"

# Atribua role Cloud Run
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:promozone-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Crie chave JSON
gcloud iam service-accounts keys create gcp-key.json \
  --iam-account=promozone-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com

# Guarde a chave em um local seguro
mkdir -p secrets
mv gcp-key.json secrets/
chmod 600 secrets/gcp-key.json
```

---

## 🚀 Deploy Local (Teste)

### Passo 1: Setup Local

```bash
# Clone o projeto
cd Desafio-Promozone

# Configure environment
bash infra/setup_local.sh
source venv/bin/activate

# Defina credenciais
export GOOGLE_APPLICATION_CREDENTIALS=$PWD/secrets/gcp-key.json
export GCP_PROJECT_ID=seu-projeto-promozone
```

### Passo 2: Criar Tabelas no BigQuery

```bash
python infra/create_tables.py $GCP_PROJECT_ID

# Output esperado:
# ✓ Dataset promozone já existe
# ✓ Tabela promotions criada
# ✓ Tabela execution_logs criada
# ✅ Todas as tabelas foram criadas/verificadas com sucesso!
```

### Passo 3: Executar Localmente

```bash
# Opção 1: Com Flask (desenvolvimento)
python -m app.main

# Opção 2: Com gunicorn (production)
pip install gunicorn
gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 "app.main:create_app()"
```

### Passo 4: Testar Endpoints

```bash
# Em outro terminal

# Health check
curl http://localhost:8080/health

# Iniciar coleta
curl -X POST http://localhost:8080/collect

# Ver estatísticas
curl http://localhost:8080/stats

# Com script automático
bash test_api.sh
```

---

## 🐳 Build e Deploy Docker Local

### Build da Imagem

```bash
# Build
docker build -t promozone-collector:latest .

# Verificar imagem
docker images | grep promozone
```

### Executar Container Localmente

```bash
docker run -p 8080:8080 \
  -e GCP_PROJECT_ID=$GCP_PROJECT_ID \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/gcp-key.json \
  -v $PWD/secrets/gcp-key.json:/app/secrets/gcp-key.json:ro \
  promozone-collector:latest

# Testar
curl http://localhost:8080/health
```

---

## ☁️ Deploy no Cloud Run

### Opção 1: Script Automático (Recomendado)

```bash
bash infra/deploy.sh seu-projeto-promozone

# Aguarde o deployment completar (2-3 minutos)
```

### Opção 2: Comandos Manuais

#### Passo 1: Push para Google Container Registry

```bash
export GCP_PROJECT_ID=seu-projeto-promozone
export SERVICE_NAME=promozone-collector

# Configure Docker para GCR
gcloud auth configure-docker

# Build e push
docker build -t gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME:latest .
docker push gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME:latest
```

#### Passo 2: Deploy no Cloud Run

```bash
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 2 \
  --timeout 120 \
  --project $GCP_PROJECT_ID \
  --set-env-vars \
    GCP_PROJECT_ID=$GCP_PROJECT_ID,\
    BIGQUERY_DATASET=promozone,\
    BIGQUERY_TABLE=promotions,\
    REQUEST_TIMEOUT=30,\
    MAX_RETRIES=3,\
    ITEMS_PER_SOURCE=25
```

#### Passo 3: Configurar Credenciais com Secret Manager

```bash
# Crie secret para credenciais
gcloud secrets create gcp-key \
  --data-file=secrets/gcp-key.json

# Atualize deployment para usar secret
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME:latest \
  --update-secrets GOOGLE_APPLICATION_CREDENTIALS=gcp-key:latest \
  --region us-central1 \
  --project $GCP_PROJECT_ID
```

#### Passo 4: Obter URL do Serviço

```bash
gcloud run services describe $SERVICE_NAME \
  --region us-central1 \
  --project $GCP_PROJECT_ID \
  --format 'value(status.url)'

# Saída: https://promozone-collector-xxxxx.run.app
```

---

## 🧪 Testar Deployment no Cloud Run

```bash
export SERVICE_URL=$(gcloud run services describe promozone-collector \
  --region us-central1 \
  --format 'value(status.url)')

# Health check
curl $SERVICE_URL/health

# Iniciar coleta
curl -X POST $SERVICE_URL/collect

# Ver estatísticas
curl $SERVICE_URL/stats
```

---

## 📊 Monitorar Execução no Cloud Run

### Ver Logs em Tempo Real

```bash
gcloud run logs read promozone-collector \
  --region us-central1 \
  --limit 100

# Ou com streaming
gcloud run logs read promozone-collector \
  --region us-central1 \
  --limit 50 \
  --follow
```

### Verificar Execução no BigQuery

```bash
# Últimas execuções
bq query --use_legacy_sql=false '
SELECT
  execution_id,
  start_time,
  end_time,
  items_collected,
  items_inserted,
  status
FROM `seu-projeto-promozone.promozone.execution_logs`
ORDER BY start_time DESC
LIMIT 10
'

# Verificar produtos coletados nas últimas 24h
bq query --use_legacy_sql=false '
SELECT
  COUNT(*) as total_items,
  COUNT(DISTINCT item_id) as unique_items,
  COUNT(DISTINCT source) as sources
FROM `seu-projeto-promozone.promozone.promotions`
WHERE collected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
'
```

---

## 🔄 Atualizar Deployment

Quando fizer alterações no código:

```bash
# 1. Build nova imagem
docker build -t gcr.io/$GCP_PROJECT_ID/promozone-collector:v2 .

# 2. Push
docker push gcr.io/$GCP_PROJECT_ID/promozone-collector:v2

# 3. Deploy nova versão
gcloud run deploy promozone-collector \
  --image gcr.io/$GCP_PROJECT_ID/promozone-collector:v2 \
  --region us-central1 \
  --project $GCP_PROJECT_ID

# Ou com tag latest
docker build -t gcr.io/$GCP_PROJECT_ID/promozone-collector:latest .
docker push gcr.io/$GCP_PROJECT_ID/promozone-collector:latest
gcloud run deploy promozone-collector --image gcr.io/$GCP_PROJECT_ID/promozone-collector:latest
```

---

## 📅 Agendar Coletas Automáticas (Cloud Scheduler)

### Criar Job de Agendamento

```bash
# Habilite Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com

# Crie job para rodar coleta a cada 6 horas
gcloud scheduler jobs create http promozone-collection \
  --schedule="0 */6 * * *" \
  --uri="$SERVICE_URL/collect" \
  --http-method=POST \
  --location=us-central1 \
  --oidc-service-account-email=promozone-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience=$SERVICE_URL

# Verificar job
gcloud scheduler jobs describe promozone-collection --location=us-central1

# Rodar manualmente para teste
gcloud scheduler jobs run promozone-collection --location=us-central1

# Ver execuções
gcloud scheduler jobs describe promozone-collection --location=us-central1
```

---

## 💰 Otimizar Custos

### BigQuery

```bash
# Usar tabelas particionadas (por data de coleta)
# Já implementado com clustering em dedupe_key

# Deletar dados antigos (exemplo: > 30 dias)
bq query --use_legacy_sql=false '
DELETE FROM `seu-projeto.promozone.promotions`
WHERE collected_at < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
'
```

### Cloud Run

```bash
# Reduzir vCPU se não precisar de 2
gcloud run deploy promozone-collector \
  --cpu=1 \
  --region us-central1

# Aumentar max latency se apropriado
gcloud run deploy promozone-collector \
  --min-instances=0 \
  --max-instances=5 \
  --region us-central1
```

---

## 🔐 Segurança - Checklist Final

- [ ] Credenciais GCP armazenadas em Secret Manager
- [ ] Service account com permissões mínimas (least privilege)
- [ ] Cloud Run sem acesso público (se necessário)
- [ ] Logs estruturados para auditoria
- [ ] CORS configurado se tiver frontend
- [ ] Limite de rate para API (opcional)

---

## 🚨 Troubleshooting

### Erro: "Permission denied" no BigQuery

```bash
# Verifique service account
gcloud iam service-accounts describe \
  promozone-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com

# Redefina credenciais
export GOOGLE_APPLICATION_CREDENTIALS=$PWD/secrets/gcp-key.json

# Recrie chave se necessário
gcloud iam service-accounts keys create secrets/gcp-key-new.json \
  --iam-account=promozone-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com
```

### Erro: "Table not found"

```bash
# Recrie tabelas
python infra/create_tables.py $GCP_PROJECT_ID

# Verifique dataset
bq ls -d
bq ls seu-projeto-promozone:promozone
```

### Cloud Run timeout

```bash
# Aumente timeout (máximo 120s)
gcloud run deploy promozone-collector \
  --timeout=120 \
  --region us-central1
```

---

## 📝 Validação Final

```bash
# Execute script de validação
bash validate.sh

# Checklist:
# ✓ Código roda localmente sem erros
# ✓ MERGE funciona (sem duplicatas)
# ✓ Logs rastreiam todos os itens processados
# ✓ README com instruções de deploy
# ✓ Docker buildável
# ✓ Cloud Run deployment completo
```

---

**Seu Promozone Collector está pronto para produção! 🚀**
