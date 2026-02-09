# Exemplo de requests para a API Promozone

## 1. Health Check
curl -X GET http://localhost:8080/health

## Response:
# {
#   "status": "healthy"
# }

---

## 2. Iniciar Coleta
curl -X POST http://localhost:8080/collect

## Response (sucesso):
# {
#   "execution_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
#   "status": "success",
#   "items_collected": 75,
#   "items_normalized": 75,
#   "items_inserted": 68,
#   "items_deduplicated": 7,
#   "duration_seconds": 23.45,
#   "start_time": "2026-02-09T10:15:30.123456",
#   "end_time": "2026-02-09T10:15:53.573456"
# }

---

## 3. Ver Estatísticas (últimas 24h)
curl -X GET http://localhost:8080/stats

## Response:
# {
#   "executions": 3,
#   "total_items": 156,
#   "unique_items": 142,
#   "by_source": {
#     "daily_offers": 52,
#     "technology": 48,
#     "electronics": 56
#   },
#   "avg_discount_percent": 18.5
# }

---

## Exemplos com jq (pretty print)

# Health check com formatting
curl -s http://localhost:8080/health | jq '.'

# Coleta com verbose
curl -v -X POST http://localhost:8080/collect | jq '.duration_seconds, .items_inserted'

# Stats com seleção de campos
curl -s http://localhost:8080/stats | jq '.by_source'

---

## Teste de performance com Apache Bench

# 10 requisições sequenciais
ab -n 10 http://localhost:8080/health

# 100 requisições com 5 conexões concorrentes
ab -n 100 -c 5 http://localhost:8080/health

---

## Curl com header customizado

curl -X POST http://localhost:8080/collect \
  -H "Content-Type: application/json" \
  -H "User-Agent: Promozone-Test/1.0"
