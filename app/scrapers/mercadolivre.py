"""
Scraper específico para Mercado Livre.
"""
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from app.scrapers.base import BaseScraper
from app.utils.logger import setup_logger
from app.utils.normalizers import (
    normalize_price,
    extract_item_id,
    normalize_text
)
from app.config import Config

logger = setup_logger(__name__)


class MercadoLivreScraper(BaseScraper):
    """Scraper para Mercado Livre."""
    
    SOURCES = {
        "daily_offers": "https://www.mercadolivre.com.br/ofertas#menu_container",
        "technology": "https://www.mercadolivre.com.br/ofertas?category=MLB1051#menu_container",
        "electronics": "https://www.mercadolivre.com.br/ofertas?container_id=MLB271545-1",
    }
    
    async def scrape_all(self) -> Dict[str, List[Dict]]:
        """
        Coleta dados de todas as fontes.
        
        Returns:
            Dicionário com itens coletados por fonte
        """
        results = {}
        
        try:
            for source_name, url in self.SOURCES.items():
                try:
                    logger.info(f"Coletando {source_name} de {url}")
                    items = await self.scrape_source(url, source_name)
                    results[source_name] = items
                    logger.info(f"Coletados {len(items)} itens de {source_name}")
                except Exception as e:
                    logger.error(f"Erro ao coletar {source_name}: {str(e)}")
                    results[source_name] = []
        
        finally:
            await self.close()
        
        return results
    
    async def scrape_source(self, url: str, source: str) -> List[Dict]:
        """
        Coleta itens de uma fonte específica.
        
        Args:
            url: URL da fonte
            source: Nome da fonte
        
        Returns:
            Lista de itens coletados
        """
        html = await self.fetch(url)
        if not html:
            return []
        
        return self._parse_items(html, source)
    
    def _parse_items(self, html: str, source: str) -> List[Dict]:
        items = []
        soup = BeautifulSoup(html, "lxml")
        
        # Seletores atualizados para o layout de Ofertas 2024/2025
        product_elements = soup.select(".poly-card") or soup.select(".promotion-item") or soup.select(".ui-search-result")
        
        if product_elements:
            for element in product_elements[:Config.ITEMS_PER_SOURCE]:
                try:
                    item = self._extract_item_data(element, source)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.debug(f"Erro ao extrair item: {str(e)}")
        
        return items

    def _extract_item_data(self, element, source: str) -> Optional[Dict]:
        try:
            # Título e URL
            link_elem = element.select_one("a.poly-component__title") or element.select_one("a")
            title = link_elem.get_text(strip=True) if link_elem else None
            url = link_elem.get("href") if link_elem else None
            
            if not title or not url: return None
            item_id = extract_item_id(url)

            # Preços (Trata a estrutura de spans aninhados do ML)
            price_elem = element.select_one(".poly-price__current .andes-money-amount__fraction")
            old_price_elem = element.select_one(".poly-price__comparison .andes-money-amount__fraction")
            
            price = normalize_price(price_elem.get_text(strip=True)) if price_elem else None
            original_price = normalize_price(old_price_elem.get_text(strip=True)) if old_price_elem else None
            
            if not price: return None

            # Imagem
            img_elem = element.select_one("img")
            image_url = img_elem.get("src") or img_elem.get("data-src")

            return {
                "marketplace": "mercadolivre",
                "item_id": item_id,
                "url": url,
                "title": title,
                "price": price,
                "original_price": original_price,
                "seller": "Mercado Livre",
                "image_url": image_url,
                "source": source,
            }
        except:
            return None