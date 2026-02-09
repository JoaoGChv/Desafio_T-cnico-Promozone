#!/bin/bash
# Script para fazer deploy no Cloud Run

set -e

PROJECT_ID=${1:-seu-projeto-gcp}
SERVICE_NAME="promozone-collector"
REGION="us-central1"
IMAGE_NAME="promozone-collector"

echo "🚀 Iniciando deploy no Cloud Run..."
echo "Projeto: $PROJECT_ID"
echo "Serviço: $SERVICE_NAME"
echo "Região: $REGION"

# 1. Autentica com GCP
echo "🔐 Autenticando com Google Cloud..."
gcloud auth configure-docker

# 2. Build da imagem Docker
echo "🔨 Build da imagem Docker..."
docker build -t gcr.io/$PROJECT_ID/$IMAGE_NAME:latest .

# 3. Push para Google Container Registry
echo "📦 Upload da imagem para GCR..."
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:latest

# 4. Deploy no Cloud Run
echo "☁️ Deploy no Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 2 \
  --timeout 120 \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID,BIGQUERY_DATASET=promozone,BIGQUERY_TABLE=promotions

echo "✅ Deploy concluído!"
echo ""
echo "📍 Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format 'value(status.url)'
