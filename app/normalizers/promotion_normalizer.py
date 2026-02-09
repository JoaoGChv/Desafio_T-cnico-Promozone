"""
Normalizador de dados de promoções.
"""
from typing import List, Dict, Optional
from app.utils.normalizers import extract_discount_percent, calculate_dedupe_key
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class PromotionNormalizer:
    """Normalizador para dados de promoções."""
    
    @staticmethod
    def normalize_items(items: List[Dict]) -> List[Dict]:
        """
        Normaliza lista de itens coletados.
        
        Args:
            items: Lista de itens brutos do scraper
        
        Returns:
            Lista de itens normalizados
        """
        normalized = []
        
        for item in items:
            try:
                normalized_item = PromotionNormalizer.normalize_item(item)
                if normalized_item:
                    normalized.append(normalized_item)
            except Exception as e:
                logger.warning(f"Erro ao normalizar item: {str(e)}")
        
        logger.info(f"Normalizados {len(normalized)} de {len(items)} itens")
        return normalized
    
    @staticmethod
    def normalize_item(item: Dict) -> Optional[Dict]:
        """
        Normaliza um único item.
        
        Args:
            item: Item a normalizar
        
        Returns:
            Item normalizado ou None se inválido
        """
        # Valida campos obrigatórios
        required_fields = ["marketplace", "item_id", "url", "title", "price"]
        for field in required_fields:
            if not item.get(field):
                logger.debug(f"Item sem campo obrigatório {field}")
                return None
        
        # Normaliza e valida preços
        price = float(item["price"]) if isinstance(item["price"], str) else item["price"]
        if price <= 0:
            logger.debug("Item com preço inválido")
            return None
        
        original_price = item.get("original_price")
        if original_price:
            original_price = float(original_price) if isinstance(original_price, str) else original_price
            if original_price <= 0:
                original_price = None
        
        # Calcula desconto
        discount_percent = extract_discount_percent(original_price, price)
        
        # Calcula dedupe_key
        dedupe_key = calculate_dedupe_key(
            item["marketplace"],
            item["item_id"],
            price
        )
        
        return {
            "marketplace": item["marketplace"],
            "item_id": item["item_id"],
            "url": item["url"],
            "title": item["title"],
            "price": price,
            "original_price": original_price,
            "discount_percent": discount_percent,
            "seller": item.get("seller") or "N/A",
            "image_url": item.get("image_url"),
            "source": item.get("source"),
            "dedupe_key": dedupe_key,
        }
