"""
Script para criar tabelas no BigQuery.
"""
from google.cloud import bigquery
import sys

def create_tables(project_id: str, dataset_id: str):
    """Cria as tabelas necessárias no BigQuery."""
    
    client = bigquery.Client(project=project_id)
    
    # 1. Tenta acessar ou criar o dataset
    dataset_ref = client.dataset(dataset_id)
    try:
        client.get_dataset(dataset_ref)
        print(f"✓ Dataset {dataset_id} já existe")
    except Exception as e:
        # Se não existir, tenta criar. Se der erro de 'Already Exists' (409), ignoramos.
        try:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            client.create_dataset(dataset, timeout=30)
            print(f"✓ Dataset {dataset_id} criado")
        except Exception as e_create:
            if "Already Exists" in str(e_create) or "409" in str(e_create):
                print(f"✓ Dataset {dataset_id} já estava presente")
            else:
                print(f"Erro crítico ao acessar dataset: {e_create}")
                sys.exit(1)
    
    # 2. Tabela de promoções
    promotions_table_id = f"{project_id}.{dataset_id}.promotions"
    
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
    
    table = bigquery.Table(promotions_table_id, schema=schema)
    table.clustering_fields = ["dedupe_key", "execution_id"]
    
    try:
        client.get_table(promotions_table_id)
        print(f"✓ Tabela promotions já existe")
    except Exception:
        table = client.create_table(table)
        print(f"✓ Tabela promotions criada")
    
    # 3. Tabela de logs
    logs_table_id = f"{project_id}.{dataset_id}.execution_logs"
    
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
    
    table = bigquery.Table(logs_table_id, schema=schema)
    
    try:
        client.get_table(logs_table_id)
        print(f"✓ Tabela execution_logs já existe")
    except Exception:
        table = client.create_table(table)
        print(f"✓ Tabela execution_logs criada")
    
    print("\n✅ Todas as tabelas foram criadas/verificadas com sucesso!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python create_tables.py <GCP_PROJECT_ID> [DATASET_ID]")
        sys.exit(1)
    
    project_id = sys.argv[1]
    dataset_id = sys.argv[2] if len(sys.argv) > 2 else "promozone"
    
    create_tables(project_id, dataset_id)
