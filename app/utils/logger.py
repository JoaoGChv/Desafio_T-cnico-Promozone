"""
Utilitários de logging estruturado.
"""
import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """Formatter para logs estruturados em JSON."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(name: str) -> logging.Logger:
    """Configure um logger estruturado."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Console handler com formatação JSON
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(JsonFormatter())
    
    logger.addHandler(console_handler)
    return logger
