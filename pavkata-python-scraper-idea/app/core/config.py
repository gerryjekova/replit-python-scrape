from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Settings
    API_TITLE: str = "Web Scraper API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Storage Settings
    STORAGE_TYPE: str = "redis"  # Options: redis, memory
    REDIS_URL: str = "redis://localhost:6379/0"

    # Task Settings
    TASK_CLEANUP_HOURS: int = 24
    MAX_CONCURRENT_TASKS: int = 5

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
