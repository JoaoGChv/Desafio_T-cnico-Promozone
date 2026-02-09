"""
Testes para funções de normalização de utilidades.
"""
import unittest
from app.utils.normalizers import (
    normalize_price,
    extract_discount_percent,
    normalize_text,
    extract_item_id,
    calculate_dedupe_key,
)


class TestNormalizers(unittest.TestCase):
    """Testes para funções de normalização."""
    
    def test_normalize_price_with_currency(self):
        """Testa normalização de preço com símbolo de moeda."""
        price = normalize_price("R$ 1.250,50")
        self.assertEqual(price, 1250.50)
    
    def test_normalize_price_without_thousands(self):
        """Testa normalização de preço sem separador de milhares."""
        price = normalize_price("R$ 100,50")
        self.assertEqual(price, 100.50)
    
    def test_normalize_price_integer(self):
        """Testa normalização de preço inteiro."""
        price = normalize_price("R$ 100,00")
        self.assertEqual(price, 100.0)
    
    def test_normalize_price_invalid(self):
        """Testa normalização de preço inválido."""
        price = normalize_price("invalido")
        self.assertIsNone(price)
    
    def test_normalize_price_empty(self):
        """Testa normalização de preço vazio."""
        price = normalize_price("")
        self.assertIsNone(price)
    
    def test_extract_discount_percent(self):
        """Testa cálculo de percentual de desconto."""
        discount = extract_discount_percent(100.0, 80.0)
        self.assertEqual(discount, 20.0)
    
    def test_extract_discount_percent_invalid(self):
        """Testa cálculo de desconto com valores inválidos."""
        discount = extract_discount_percent(0, 50.0)
        self.assertIsNone(discount)
        
        discount = extract_discount_percent(100.0, None)
        self.assertIsNone(discount)
    
    def test_normalize_text_extra_spaces(self):
        """Testa normalização de texto com espaços extras."""
        text = normalize_text("  Produto   com   espaços  ")
        self.assertEqual(text, "Produto com espaços")
    
    def test_normalize_text_empty(self):
        """Testa normalização de texto vazio."""
        text = normalize_text("")
        self.assertEqual(text, "")
    
    def test_extract_item_id_valid(self):
        """Testa extração de item ID válido."""
        url = "https://www.mercadolivre.com.br/produto-teste/MLB123456789"
        item_id = extract_item_id(url)
        self.assertEqual(item_id, "MLB123456789")
    
    def test_extract_item_id_invalid(self):
        """Testa extração de item ID inválido."""
        url = "https://www.example.com/produto"
        item_id = extract_item_id(url)
        self.assertIsNone(item_id)
    
    def test_calculate_dedupe_key(self):
        """Testa cálculo de chave de deduplicação."""
        key = calculate_dedupe_key("mercadolivre", "MLB123", 100.50)
        self.assertEqual(key, "mercadolivre#MLB123#100.5")


if __name__ == "__main__":
    unittest.main()
