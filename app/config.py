"""
Configurações da aplicação.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurações padrão."""
    
    # BigQuery
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "seu-projeto-gcp")
    BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "promozone")
    BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE", "promotions")
    BIGQUERY_LOG_TABLE = os.getenv("BIGQUERY_LOG_TABLE", "execution_logs")
    
    # Scraper
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    BACKOFF_FACTOR = float(os.getenv("BACKOFF_FACTOR", "1.5"))
    ITEMS_PER_SOURCE = int(os.getenv("ITEMS_PER_SOURCE", "25"))
    
    # Flask
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    # Credenciais GCP
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", 
        ""
    )
