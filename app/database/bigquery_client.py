import logging
import uuid
from datetime import datetime  # <--- Adicione esta linha
from typing import List, Dict, Tuple, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
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
            self.client = bigquery.Client(project=self.project_id)
            logger.info(f"BigQuery client inicializado para projeto {self.project_id}")
        except Exception as e:
            logger.error(f"Erro ao inicializar BigQuery: {str(e)}")
            raise
    
    def ensure_tables_exist(self) -> bool:
        """
        Cria tabelas se não existirem.
        
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            self._create_promotions_table()
            self._create_logs_table()
            logger.info("Tabelas do BigQuery verificadas/criadas com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {str(e)}")
            return False
    
    def _create_promotions_table(self):
        """Cria tabela de promoções se não existir."""
        table_id = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        
        schema = [
            bigquery.SchemaField("marketplace", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("item_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("url", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("price", "NUMERIC", mode="REQUIRED"),
            bigquery.SchemaField("original_price", "NUMERIC", mode="NULLABLE"),
            bigquery.SchemaField("discount_percent", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("seller", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("image_url", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("dedupe_key", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("execution_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("collected_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("inserted_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        table = bigquery.Table(table_id, schema=schema)
        table.clustering_fields = ["dedupe_key", "execution_id"]
        
        try:
            existing = self.client.get_table(table_id)
            logger.debug(f"Tabela {table_id} já existe")
        except Exception:
            table = self.client.create_table(table)
            logger.info(f"Tabela {table_id} criada com sucesso")
    
    def _create_logs_table(self):
        """Cria tabela de logs se não existir."""
        table_id = f"{self.project_id}.{self.dataset_id}.{self.log_table_id}"
        
        schema = [
            bigquery.SchemaField("execution_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("start_time", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("end_time", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("items_collected", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("items_inserted", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("items_deduplicated", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("error_message", "STRING", mode="NULLABLE"),
        ]
        
        table = bigquery.Table(table_id, schema=schema)
        
        try:
            existing = self.client.get_table(table_id)
            logger.debug(f"Tabela {table_id} já existe")
        except Exception:
            table = self.client.create_table(table)
            logger.info(f"Tabela {table_id} criada com sucesso")
    
    def merge_promotions(self, rows_to_insert: List[Dict], execution_id: str) -> Tuple[int, int]:
        """Realiza o MERGE usando uma tabela temporária (versão corrigida para nulos)."""
        if not rows_to_insert:
            return 0, 0

        formatted_rows = []
        for r in rows_to_insert:
            # Garantimos que nenhum valor numérico seja None antes de passar para float()
            price = r.get('price')
            original_price = r.get('original_price')
            discount = r.get('discount_percent')

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
        
        try:
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",
                # Forçamos o schema para garantir que o BigQuery aceite os nulos no original_price
                schema=[
                    bigquery.SchemaField("original_price", "NUMERIC", mode="NULLABLE"),
                ]
            )
            load_job = self.client.load_table_from_json(formatted_rows, temp_table_id, job_config=job_config)
            load_job.result()

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
            logger.error(f"Erro no fluxo: {str(e)}")
            self.client.delete_table(temp_table_id, not_found_ok=True)
            raise
