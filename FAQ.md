# ❓ FAQ - Promozone Collector

## Instalação e Setup

### P: Como fazer setup local?
**R:**
```bash
bash quickstart.sh 1
# ou manualmente
bash infra/setup_local.sh
source venv/bin/activate
```

### P: Qual versão de Python é necessária?
**R:** Python 3.11+ (está no Dockerfile e no requirements.txt)

### P: Como obter credenciais GCP?
**R:**
```bash
# 1. Criar service account
gcloud iam service-accounts create promozone-collector

# 2. Atribuir roles
gcloud projects add-iam-policy-binding seu-projeto \
  --member="serviceAccount:..." --role="roles/bigquery.admin"

# 3. Criar chave JSON
gcloud iam service-accounts keys create key.json \
  --iam-account=promozone-collector@seu-projeto.iam.gserviceaccount.com

# 4. Definir variável
export GOOGLE_APPLICATION_CREDENTIALS=$PWD/key.json
```

---

## Configuração

### P: Devo hardcodar credenciais?
**R:** **NUNCA!** Use variáveis de ambiente:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
export GCP_PROJECT_ID=seu-projeto
```

### P: Como customizar quantidade de itens coletados?
**R:** Edite `.env`:
```bash
ITEMS_PER_SOURCE=30  # Default é 25
```

### P: Qual é o timeout padrão para requisições?
**R:** 30 segundos, configurável:
```bash
REQUEST_TIMEOUT=60  # Em .env
```

### P: Como aumentar tentativas de retry?
**R:** Configure em `.env`:
```bash
MAX_RETRIES=5          # Default é 3
BACKOFF_FACTOR=2.0     # Default é 1.5
```

---

## Banco de Dados

### P: Como criar tabelas no BigQuery?
**R:**
```bash
python infra/create_tables.py seu-projeto-gcp
```

### P: Como verificar se tabelas foram criadas?
**R:**
```bash
bq ls seu-projeto:promozone
bq show seu-projeto:promozone.promotions
```

### P: O que é dedupe_key?
**R:** Chave de deduplicação composta por: `marketplace#item_id#price`
Previne que o mesmo produto com o mesmo preço seja inserido duas vezes.

### P: Como o MERGE funciona?
**R:** SQL MERGE automático:
- Se `dedupe_key` já existe → UPDATE (atualiza alguns campos)
- Se é novo → INSERT (insere novo registro)

### P: Como validar deduplicação?
**R:**
```sql
SELECT dedupe_key, COUNT(*) as count
FROM `seu-projeto.promozone.promotions`
WHERE collected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY dedupe_key
HAVING COUNT(*) > 1;
-- Resultado vazio = sem duplicatas ✓
```

---

## Scraper

### P: Quantas fontes são coletadas?
**R:** 3 fontes do Mercado Livre:
1. Ofertas do Dia: https://www.mercadolivre.com.br/ofertas#menu_container
2. Tecnologia: https://www.mercadolivre.com.br/ofertas?category=MLB1051
3. Eletrônicos: https://www.mercadolivre.com.br/ofertas?container_id=MLB271545-1

### P: Como o scraper lida com falhas?
**R:** Exponential backoff automático:
```
Tentativa 1: imediato
Tentativa 2: 1.0s * 1.5 = 1.5s
Tentativa 3: 1.0s * 1.5² = 2.25s
Máximo 3 tentativas por padrão
```

### P: Por que os User-Agents mudam?
**R:** Para simular requisições reais e evitar bloqueios por anti-bots.

### P: Como normalizar "R$ 1.250,50"?
**R:**
```python
from app.utils.normalizers import normalize_price
price = normalize_price("R$ 1.250,50")  # Retorna 1250.50
```

### P: Como calcular percentual de desconto?
**R:**
```python
from app.utils.normalizers import extract_discount_percent
discount = extract_discount_percent(100.0, 80.0)  # Retorna 20.0
```

---

## API

### P: Como testar a API?
**R:**
```bash
# Health check
curl http://localhost:8080/health

# Iniciar coleta
curl -X POST http://localhost:8080/collect

# Estatísticas
curl http://localhost:8080/stats

# Com script automático
bash test_api.sh
```

### P: Qual é o formato do response de /collect?
**R:**
```json
{
  "execution_id": "uuid-string",
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

### P: Quanto tempo leva uma coleta?
**R:** 20-30 segundos típico (3 fontes x ~5-10s cada + BQ)

### P: Como rastrear execuções?
**R:** Use `execution_id` para correlacionar logs:
```sql
SELECT * FROM `seu-projeto.promozone.execution_logs`
WHERE execution_id = 'seu-uuid'
```

### P: Posso rodar múltiplas coletas em paralelo?
**R:** Sim, Cloud Run suporta escalabilidade automática. Cada execução tem seu próprio `execution_id`.

---

## Docker e Cloud Run

### P: Como buildar a imagem Docker?
**R:**
```bash
docker build -t promozone-collector:latest .
docker run -p 8080:8080 \
  -e GCP_PROJECT_ID=seu-projeto \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/gcp-key.json \
  -v /caminho/key.json:/app/secrets/gcp-key.json:ro \
  promozone-collector:latest
```

### P: Como fazer deploy no Cloud Run?
**R:**
```bash
bash infra/deploy.sh seu-projeto-gcp
# ou automaticamente
bash quickstart.sh 5
```

### P: Qual é a URL do Cloud Run após deploy?
**R:**
```bash
gcloud run services describe promozone-collector \
  --region us-central1 \
  --format 'value(status.url)'
```

### P: Como aumentar memória do Cloud Run?
**R:**
```bash
gcloud run deploy promozone-collector \
  --memory 2Gi --cpu 2 --region us-central1
```

### P: Como ver logs do Cloud Run?
**R:**
```bash
gcloud run logs read promozone-collector --limit 100
gcloud run logs read promozone-collector --follow  # streaming
```

---

## Testes

### P: Como rodar testes?
**R:**
```bash
python -m pytest tests/ -v
bash test_api.sh  # Testa endpoints
bash validate.sh   # Valida implementação
```

### P: Quais testes existem?
**R:**
- `test_normalizer.py`: Normalização de promoções
- `test_utils.py`: Funções utilitárias
- Testes de API via curl

### P: Como fazer cobertura de testes?
**R:**
```bash
pip install pytest-cov
pytest tests/ --cov=app --cov-report=html
```

---

## Troubleshooting

### P: Erro: "Permission denied" no BigQuery
**R:**
```bash
# Verifique credenciais
gcloud auth list
export GOOGLE_APPLICATION_CREDENTIALS=/caminho/correto/key.json

# Redefina chave se necessário
gcloud iam service-accounts keys create new-key.json \
  --iam-account=promozone-collector@seu-projeto.iam.gserviceaccount.com
```

### P: Erro: "Table not found"
**R:**
```bash
# Recrie as tabelas
python infra/create_tables.py seu-projeto-gcp

# Verifique dataset
bq ls seu-projeto:promozone
```

### P: Scraper não coleta itens
**R:**
- Mercado Livre pode ter mudado a estrutura HTML
- Aumente `REQUEST_TIMEOUT` se muito lento
- Verifique seletores CSS em `app/scrapers/mercadolivre.py`

### P: Cloud Run timeout
**R:**
```bash
gcloud run deploy promozone-collector \
  --timeout 120 \
  --region us-central1
```

### P: Virtual environment não ativa
**R:**
```bash
# Recrie
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### P: Erro de importação do módulo
**R:**
```bash
# Verifique __init__.py em cada diretório
# Adicione ao PYTHONPATH se necessário
export PYTHONPATH=$PYTHONPATH:$PWD
```

---

## Performance e Otimização

### P: Como melhorar performance?
**R:**
1. Aumentar `ITEMS_PER_SOURCE` (mais itens)
2. Reduzir `REQUEST_TIMEOUT` (se site rápido)
3. Aumentar vCPU no Cloud Run
4. Usar cache para itens duplicados

### P: Quanto custa rodar no GCP?
**R:**
- **BigQuery**: ~$6 por TB de dados consultado
- **Cloud Run**: $0.00001667 por vCPU-segundo
- **Storage**: ~$0.02 por GB/mês
- Primeiros 1M requisições/mês são gratuitas

### P: Como reduzir custos?
**R:**
1. Usar clustering (já implementado)
2. Particionar por data de coleta
3. Deletar dados antigos
4. Usar min-instances=0 no Cloud Run

---

## Segurança

### P: Como armazenar credenciais com segurança?
**R:**
```bash
# Local: variáveis de ambiente
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# Cloud Run: Secret Manager
gcloud secrets create gcp-key --data-file=key.json
gcloud run deploy promozone-collector \
  --update-secrets GOOGLE_APPLICATION_CREDENTIALS=gcp-key:latest
```

### P: Como restringir acesso à API?
**R:**
```bash
# Remover --allow-unauthenticated do deploy
gcloud run deploy promozone-collector \
  --image gcr.io/seu-projeto/promozone-collector \
  # Sem --allow-unauthenticated

# Usar IAM para controlar quem pode chamar
```

### P: Como fazer auditoria das coletas?
**R:**
```sql
SELECT execution_id, start_time, items_collected, status
FROM `seu-projeto.promozone.execution_logs`
WHERE start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
ORDER BY start_time DESC;
```

---

## Extensão e Customização

### P: Como adicionar nova fonte de dados?
**R:**
1. Crie novo arquivo em `app/scrapers/nova_fonte.py`
2. Herde de `BaseScraper`
3. Implemente método `scrape_source()`
4. Adicione em `app/main.py` no endpoint `/collect`

### P: Como adicionar novo campo na tabela?
**R:**
```python
# 1. Edite schema em app/database/bigquery_client.py
schema.append(bigquery.SchemaField("novo_campo", "STRING"))

# 2. Recrie tabela
python infra/create_tables.py seu-projeto

# 3. Atualize normalizer
```

### P: Como integrar com outro banco de dados?
**R:**
Crie novo cliente em `app/database/` e implemente:
- `ensure_tables_exist()`
- `merge_promotions()`
- `log_execution()`

---

## Documentação

### P: Onde estão as queries SQL úteis?
**R:** Em `README.md` → seção "Queries SQL Úteis"

### P: Como entender a arquitetura?
**R:** Leia:
1. `README.md` - Visão geral
2. `IMPLEMENTATION_SUMMARY.md` - Decisões técnicas
3. `DEPLOY.md` - Deploy step-by-step

### P: Onde estão os exemplos de API?
**R:** Em `REQUESTS.md`

---

## Suporte

### P: Como encontrar logs?
**R:**
```bash
# Local
cat app.log  # gerado automaticamente

# Cloud Run
gcloud run logs read promozone-collector --limit 100

# BigQuery logs de execução
SELECT * FROM `seu-projeto.promozone.execution_logs`
```

### P: Qual arquivo devo editar para customizar?
**R:** Comece por:
- `app/config.py` - configurações
- `app/scrapers/mercadolivre.py` - fontes de dados
- `.env` - variáveis de ambiente

### P: Como reportar um bug?
**R:** Verifique:
1. Logs estruturados em JSON
2. Variáveis de ambiente
3. Permissões GCP
4. Conectividade com BigQuery

---

## Checklist Final

- [ ] Código roda localmente
- [ ] Tabelas criadas no BigQuery
- [ ] MERGE funciona (sem duplicatas)
- [ ] 3 endpoints funcionam
- [ ] Docker buildar
- [ ] Testes passam
- [ ] README atualizado
- [ ] Credenciais seguras
- [ ] Deploy no Cloud Run OK
- [ ] Monitores configurados

---

**Mais dúvidas? Verifique:**
- README.md (visão geral)
- DEPLOY.md (deployment)
- IMPLEMENTATION_SUMMARY.md (arquitetura)
- REQUESTS.md (exemplos)
- validate.sh (validação)
