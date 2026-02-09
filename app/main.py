"""
Aplicação Flask principal.
"""
from flask import Flask, jsonify, request
from datetime import datetime
import uuid
import asyncio
from app.config import Config
from app.scrapers.mercadolivre import MercadoLivreScraper
from app.normalizers.promotion_normalizer import PromotionNormalizer
from app.database.bigquery_client import BigQueryClient
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_app():
    """Factory function para criar a aplicação Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializa BigQuery
    try:
        bq_client = BigQueryClient()
        bq_client.ensure_tables_exist()
    except Exception as e:
        logger.error(f"Erro ao inicializar BigQuery: {str(e)}")
    
    @app.route("/health", methods=["GET"])
    def health():
        """Endpoint de health check."""
        return jsonify({"status": "healthy"}), 200
    
    @app.route("/collect", methods=["POST"])
    def collect():
        """
        Endpoint para coletar promoções.
        
        Realiza o ciclo completo:
        1. Scraping de múltiplas fontes
        2. Normalização de dados
        3. MERGE no BigQuery
        4. Registro de logs
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Iniciando coleta com execution_id: {execution_id}")
        
        try:
            # Scraping
            scraper = MercadoLivreScraper()
            scrape_results = asyncio.run(scraper.scrape_all())
            
            # Combina resultados de todas as fontes
            all_items = []
            items_collected = 0
            
            for source_name, items in scrape_results.items():
                all_items.extend(items)
                items_collected += len(items)
            
            logger.info(f"Coletados {items_collected} itens de {len(scrape_results)} fontes")
            
            # Normalização
            normalized_items = PromotionNormalizer.normalize_items(all_items)
            
            # Persistência no BigQuery
            bq_client = BigQueryClient()
            items_inserted, items_deduplicated = bq_client.merge_promotions(
                normalized_items,
                execution_id
            )
            
            # Logs
            end_time = datetime.utcnow()
            duration_seconds = (end_time - start_time).total_seconds()
            
            bq_client.log_execution(
                execution_id=execution_id,
                start_time=start_time,
                end_time=end_time,
                items_collected=items_collected,
                items_inserted=items_inserted,
                items_deduplicated=items_deduplicated,
                status="success"
            )
            
            logger.info(
                f"Coleta finalizada com sucesso. "
                f"Coletados: {items_collected}, "
                f"Inseridos: {items_inserted}, "
                f"Duplicados: {items_deduplicated}, "
                f"Duração: {duration_seconds:.2f}s"
            )
            
            return jsonify({
                "execution_id": execution_id,
                "status": "success",
                "items_collected": items_collected,
                "items_normalized": len(normalized_items),
                "items_inserted": items_inserted,
                "items_deduplicated": items_deduplicated,
                "duration_seconds": duration_seconds,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }), 200
        
        except Exception as e:
            end_time = datetime.utcnow()
            duration_seconds = (end_time - start_time).total_seconds()
            
            logger.error(f"Erro durante coleta: {str(e)}", exc_info=True)
            
            # Registra erro nos logs
            try:
                bq_client = BigQueryClient()
                bq_client.log_execution(
                    execution_id=execution_id,
                    start_time=start_time,
                    end_time=end_time,
                    items_collected=0,
                    items_inserted=0,
                    items_deduplicated=0,
                    status="error",
                    error_message=str(e)
                )
            except Exception as log_error:
                logger.error(f"Erro ao registrar log de erro: {str(log_error)}")
            
            return jsonify({
                "execution_id": execution_id,
                "status": "error",
                "error": str(e),
                "duration_seconds": duration_seconds,
            }), 500
    
    @app.route("/stats", methods=["GET"])
    def stats():
        """Endpoint para obter estatísticas."""
        try:
            bq_client = BigQueryClient()
            
            # Query para últimas 24h
            query = f"""
            SELECT
                COUNT(DISTINCT execution_id) as executions,
                COUNT(*) as total_items,
                COUNT(DISTINCT item_id) as unique_items,
                SUM(CASE WHEN source = 'daily_offers' THEN 1 ELSE 0 END) as daily_offers,
                SUM(CASE WHEN source = 'technology' THEN 1 ELSE 0 END) as technology,
                SUM(CASE WHEN source = 'electronics' THEN 1 ELSE 0 END) as electronics,
                AVG(discount_percent) as avg_discount
            FROM `{Config.GCP_PROJECT_ID}.{Config.BIGQUERY_DATASET}.{Config.BIGQUERY_TABLE}`
            WHERE collected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
            """
            
            query_job = bq_client.client.query(query)
            results = query_job.result()
            
            row = next(results)
            
            return jsonify({
                "executions": row.executions,
                "total_items": row.total_items,
                "unique_items": row.unique_items,
                "by_source": {
                    "daily_offers": row.daily_offers,
                    "technology": row.technology,
                    "electronics": row.electronics,
                },
                "avg_discount_percent": float(row.avg_discount) if row.avg_discount else 0,
            }), 200
        
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=Config.DEBUG)
