#!/bin/bash
# Script para testar a API localmente

API_URL="http://localhost:8080"

echo "🧪 Testando API Promozone"
echo "========================="
echo ""

# 1. Health check
echo "1️⃣  Testando /health"
curl -s "$API_URL/health" | python -m json.tool
echo ""

# 2. Coleta (isso pode levar tempo)
echo "2️⃣  Testando /collect (isso pode levar alguns minutos)"
START_TIME=$(date +%s)
RESPONSE=$(curl -s -X POST "$API_URL/collect")
END_TIME=$(date +%s)

echo "$RESPONSE" | python -m json.tool

# Extrai execution_id
EXECUTION_ID=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('execution_id', 'N/A'))" 2>/dev/null)
echo "Execution ID: $EXECUTION_ID"
echo "Tempo total: $((END_TIME - START_TIME)) segundos"
echo ""

# 3. Stats
echo "3️⃣  Testando /stats"
curl -s "$API_URL/stats" | python -m json.tool
echo ""

echo "✅ Testes concluídos!"
