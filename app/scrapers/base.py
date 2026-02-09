"""
Scraper base com lógica comum de requisições.
"""
import httpx
import time
from typing import Optional
from app.utils.logger import setup_logger
from app.config import Config

logger = setup_logger(__name__)


class BaseScraper:
    """Classe base para scrapers com retry e politesse."""
    
    # User agents variados para polidez
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
    ]
    
    HEADERS_BASE = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    def __init__(self):
        """Inicializa o scraper."""
        self.client = None
        self.max_retries = Config.MAX_RETRIES
        self.backoff_factor = Config.BACKOFF_FACTOR
        self.timeout = Config.REQUEST_TIMEOUT
    
    def get_headers(self) -> dict:
        """Retorna headers com User-Agent aleatório."""
        import random
        headers = self.HEADERS_BASE.copy()
        headers["User-Agent"] = random.choice(self.USER_AGENTS)
        return headers
    
    async def fetch(self, url: str) -> Optional[str]:
        """
        Faz requisição HTTP com retry e exponential backoff.
        
        Args:
            url: URL a requisitar
        
        Returns:
            Conteúdo HTML ou None se falhar
        """
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(url, headers=self.get_headers())
                response.raise_for_status()
                return response.text
            
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Erro ao requisitar {url} (tentativa {attempt + 1}/{self.max_retries}): {str(e)}"
                )
                
                if attempt < self.max_retries - 1:
                    delay = 1.0 * (self.backoff_factor ** attempt)
                    time.sleep(delay)
        
        logger.error(f"Falha ao requisitar {url} após {self.max_retries} tentativas")
        raise last_exception
    
    async def close(self):
        """Fecha o cliente HTTP."""
        if self.client:
            await self.client.aclose()
