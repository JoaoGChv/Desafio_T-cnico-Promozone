"""
Testes para o normalizer de promoções.
"""
import unittest
from app.normalizers.promotion_normalizer import PromotionNormalizer


class TestPromotionNormalizer(unittest.TestCase):
    """Testes para normalização de promoções."""
    
    def test_normalize_valid_item(self):
        """Testa normalização de item válido."""
        item = {
            "marketplace": "mercadolivre",
            "item_id": "MLB123456789",
            "url": "https://example.com",
            "title": "Produto Teste",
            "price": 100.50,
            "original_price": 150.00,
            "seller": "Vendedor Teste",
            "image_url": "https://image.url",
            "source": "daily_offers",
        }
        
        result = PromotionNormalizer.normalize_item(item)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["marketplace"], "mercadolivre")
        self.assertEqual(result["item_id"], "MLB123456789")
        self.assertEqual(result["price"], 100.50)
        self.assertIsNotNone(result["discount_percent"])
    
    def test_normalize_item_without_original_price(self):
        """Testa normalização sem preço original."""
        item = {
            "marketplace": "mercadolivre",
            "item_id": "MLB987654321",
            "url": "https://example.com",
            "title": "Produto Sem Desconto",
            "price": 50.00,
            "source": "technology",
        }
        
        result = PromotionNormalizer.normalize_item(item)
        
        self.assertIsNotNone(result)
        self.assertIsNone(result["discount_percent"])
    
    def test_normalize_item_missing_required_field(self):
        """Testa normalização com campo obrigatório faltando."""
        item = {
            "marketplace": "mercadolivre",
            "item_id": "MLB123456789",
            "url": "https://example.com",
            # Falta título
            "price": 100.50,
            "source": "electronics",
        }
        
        result = PromotionNormalizer.normalize_item(item)
        
        self.assertIsNone(result)
    
    def test_normalize_item_invalid_price(self):
        """Testa normalização com preço inválido."""
        item = {
            "marketplace": "mercadolivre",
            "item_id": "MLB123456789",
            "url": "https://example.com",
            "title": "Produto Teste",
            "price": 0,  # Preço inválido
            "source": "daily_offers",
        }
        
        result = PromotionNormalizer.normalize_item(item)
        
        self.assertIsNone(result)
    
    def test_normalize_items_batch(self):
        """Testa normalização em lote."""
        items = [
            {
                "marketplace": "mercadolivre",
                "item_id": "MLB1",
                "url": "https://example.com/1",
                "title": "Produto 1",
                "price": 100.00,
                "source": "daily_offers",
            },
            {
                "marketplace": "mercadolivre",
                "item_id": "MLB2",
                "url": "https://example.com/2",
                "title": "Produto 2",
                "price": 200.00,
                "original_price": 250.00,
                "source": "technology",
            },
            {
                # Item inválido será filtrado
                "marketplace": "mercadolivre",
                "item_id": "MLB3",
                "url": "https://example.com/3",
                "title": "",  # Título vazio
                "price": 300.00,
                "source": "electronics",
            },
        ]
        
        result = PromotionNormalizer.normalize_items(items)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["item_id"], "MLB1")
        self.assertEqual(result[1]["item_id"], "MLB2")


if __name__ == "__main__":
    unittest.main()
