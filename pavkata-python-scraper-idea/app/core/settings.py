from pydantic import BaseSettings, HttpUrl
from typing import Optional, Dict, Any
from pathlib import Path

class Settings(BaseSettings):
    # API Settings
    API_VERSION: str = "1.0.0"
    API_TITLE: str = "Web Scraper API"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Crawler Settings
    CRAWL4AI_API_KEY: str
    MAX_CONCURRENT_TASKS: int = 10
    TASK_TIMEOUT: int = 300
    
    # Storage Settings
    CONFIG_DIR: Path = Path("configs")
    STORAGE_TYPE: str = "memory"  # Options: memory, redis, file
    REDIS_URL: Optional[str] = None
    
    # Task Settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 60
    
    # Proxy Settings
    USE_PROXIES: bool = False
    PROXY_URL: Optional[HttpUrl] = None
    PROXY_AUTH: Optional[Dict[str, str]] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create global settings instance
settings = Settings()