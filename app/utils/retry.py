"""
Utilitários de retry com exponential backoff.
"""
import asyncio
from typing import Callable, Any, TypeVar
from functools import wraps
import random

T = TypeVar('T')

def exponential_backoff_retry(
    max_retries: int = 3,
    backoff_factor: float = 1.5,
    base_delay: float = 1.0
):
    """
    Decorator para retry com exponential backoff.
    
    Args:
        max_retries: Número máximo de tentativas
        backoff_factor: Multiplicador para cada retry
        base_delay: Delay inicial em segundos
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (backoff_factor ** attempt)
                        # Adiciona jitter para evitar thundering herd
                        jitter = random.uniform(0, delay * 0.1)
                        await asyncio.sleep(delay + jitter)
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (backoff_factor ** attempt)
                        jitter = random.uniform(0, delay * 0.1)
                        asyncio.get_event_loop().run_until_complete(
                            asyncio.sleep(delay + jitter)
                        )
            
            raise last_exception
        
        # Retorna a versão apropriada (async ou sync)
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
