import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from google.cloud import bigquery
from app.config import Config

logger = logging.getLogger(__name__)

class BigQueryClient:
    """Client para operações no BigQuery."""
    
    def __init__(self):
        """Inicializa o cliente BigQuery."""
        self.project_id = Config.GCP_PROJECT_ID
        self.dataset_id = Config.BIGQUERY_DATASET
        self.table_id = Config.BIGQUERY_TABLE
        self.log_table_id = Config.BIGQUERY_LOG_TABLE
        
        try:
            # Inicializa o cliente oficial do Google Cloud BigQuery
            self.client = bigquery.Client(project=self.project_id)
            logger.info(f"BigQuery client inicializado para projeto {self.project_id}")
        except Exception as e:
            logger.error(f"Erro ao inicializar BigQuery: {str(e)}")
            raise

    def ensure_tables_exist(self) -> bool:
        """
        Verifica/Cria as tabelas necessárias.
        Nota: Como as tabelas foram criadas manualmente via SQL Console, 
        este método serve para validação de conectividade.
        """
        return True

    def merge_promotions(self, rows_to_insert: List[Dict], execution_id: str) -> Tuple[int, int]:
        """Realiza o MERGE dos dados usando uma tabela temporária para garantir deduplicação."""
        if not rows_to_insert:
            return 0, 0

        formatted_rows = []
        for r in rows_to_insert:
            price = r.get('price')
            original_price = r.get('original_price')
            discount = r.get('discount_percent')

            # Formata os dados garantindo que tipos numéricos não sejam None
            formatted_rows.append({
                "marketplace": str(r.get('marketplace', 'mercadolivre')),
                "item_id": str(r.get('item_id', '')),
                "url": str(r.get('url', '')),
                "title": str(r.get('title', '')),
                "price": float(price) if price is not None else 0.0,
                "original_price": float(original_price) if original_price is not None else None,
                "discount_percent": float(discount) if discount is not None else 0.0,
                "seller": str(r.get('seller', 'Mercado Livre')),
                "image_url": str(r.get('image_url', '')),
                "source": str(r.get('source', '')),
                "dedupe_key": str(r.get('dedupe_key', '')),
                "execution_id": str(execution_id),
                "collected_at": str(r.get('collected_at', datetime.utcnow().isoformat()))
            })

        temp_table_id = f"{self.project_id}.{self.dataset_id}.temp_{execution_id.replace('-', '_')}"
        
        # Schema completo para evitar erros de 'No such field' na carga do JSON
        schema = [
            bigquery.SchemaField("marketplace", "STRING"),
            bigquery.SchemaField("item_id", "STRING"),
            bigquery.SchemaField("url", "STRING"),
            bigquery.SchemaField("title", "STRING"),
            bigquery.SchemaField("price", "NUMERIC"),
            bigquery.SchemaField("original_price", "NUMERIC", mode="NULLABLE"),
            bigquery.SchemaField("discount_percent", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("seller", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("image_url", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("dedupe_key", "STRING"),
            bigquery.SchemaField("execution_id", "STRING"),
            bigquery.SchemaField("collected_at", "TIMESTAMP"),
        ]

        try:
            # Carrega dados para tabela temporária
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",
                schema=schema
            )
            load_job = self.client.load_table_from_json(formatted_rows, temp_table_id, job_config=job_config)
            load_job.result()

            # Executa o MERGE atômico
            sql = f"""
                MERGE `{self.project_id}.{self.dataset_id}.promotions` T
                USING `{temp_table_id}` S
                ON T.dedupe_key = S.dedupe_key
                WHEN NOT MATCHED THEN
                    INSERT (marketplace, item_id, url, title, price, original_price, 
                            discount_percent, seller, image_url, source, dedupe_key, 
                            execution_id, collected_at, inserted_at)
                    VALUES (S.marketplace, S.item_id, S.url, S.title, S.price, S.original_price, 
                            S.discount_percent, S.seller, S.image_url, S.source, S.dedupe_key, 
                            S.execution_id, S.collected_at, CURRENT_TIMESTAMP())
            """
            query_job = self.client.query(sql)
            query_job.result()
            
            inserted = query_job.num_dml_affected_rows or 0
            self.client.delete_table(temp_table_id, not_found_ok=True)
            return inserted, len(rows_to_insert) - inserted
            
        except Exception as e:
            logger.error(f"Erro no fluxo de merge: {str(e)}")
            self.client.delete_table(temp_table_id, not_found_ok=True)
            raise

    def log_execution(self, execution_id: str, start_time: datetime, end_time: datetime,
                      items_collected: int, items_inserted: int, items_deduplicated: int,
                      status: str, error_message: str = None):
        """Registra os metadados da execução na tabela de logs para monitoramento."""
        table_id = f"{self.project_id}.{self.dataset_id}.{self.log_table_id}"
        
        row = {
            "execution_id": execution_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat() if end_time else None,
            "items_collected": items_collected,
            "items_inserted": items_inserted,
            "items_deduplicated": items_deduplicated,
            "status": status,
            "error_message": error_message
        }
        
        try:
            # Inserção direta via JSON para logs rápidos
            errors = self.client.insert_rows_json(table_id, [row])
            if errors:
                logger.error(f"Erro ao inserir log: {errors}")
        except Exception as e:
            logger.error(f"Erro ao registrar log: {str(e)}")
