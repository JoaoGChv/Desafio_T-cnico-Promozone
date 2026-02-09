"""
Utilitários de normalização de dados.
"""
import re
from typing import Optional
from decimal import Decimal, InvalidOperation

def normalize_price(price_str: str) -> Optional[float]:
    """
    Normaliza string de preço no formato "R$ 1.250,50" para decimal.
    
    Args:
        price_str: String com o preço (ex: "R$ 1.250,50")
    
    Returns:
        Float com o preço normalizado ou None se inválido
    """
    if not price_str:
        return None
    
    # Remove "R$" e espaços
    clean = price_str.replace("R$", "").strip()
    
    # Remove pontos (milhares) e substitui vírgula por ponto
    clean = clean.replace(".", "").replace(",", ".")
    
    try:
        return float(clean)
    except ValueError:
        return None


def extract_discount_percent(
    original_price: Optional[float],
    current_price: Optional[float]
) -> Optional[float]:
    """
    Calcula percentual de desconto.
    
    Args:
        original_price: Preço original
        current_price: Preço com desconto
    
    Returns:
        Percentual de desconto ou None se inválido
    """
    if (not original_price or not current_price or 
        original_price <= 0 or current_price <= 0):
        return None
    
    try:
        discount = ((original_price - current_price) / original_price) * 100
        return round(discount, 2)
    except (ZeroDivisionError, TypeError):
        return None


def normalize_text(text: str) -> str:
    """
    Normaliza texto removendo espaços extras e caracteres especiais.
    
    Args:
        text: Texto a normalizar
    
    Returns:
        Texto normalizado
    """
    if not text:
        return ""
    
    # Remove espaços extras
    text = " ".join(text.split())
    return text.strip()


def extract_item_id(url: str) -> Optional[str]:
    """
    Extrai item_id da URL do Mercado Livre.
    
    Args:
        url: URL do produto
    
    Returns:
        Item ID ou None se não encontrado
    """
    if not url:
        return None
    
    # Padrão: /MLB123456789
    match = re.search(r'MLB\d+', url)
    if match:
        return match.group(0)
    
    return None


def calculate_dedupe_key(marketplace: str, item_id: str, price: float) -> str:
    """
    Calcula chave de deduplicação.
    
    Args:
        marketplace: Nome do marketplace
        item_id: ID do item
        price: Preço do item
    
    Returns:
        Chave de deduplicação
    """
    return f"{marketplace}#{item_id}#{price}"
