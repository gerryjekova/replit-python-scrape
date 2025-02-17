from pydantic_settings import BaseSettings
from datetime import datetime
import pytz


class Settings(BaseSettings):
    # User Settings
    CURRENT_USER: str = "gerryjekova"

    # Time Settings
    @property
    def CURRENT_TIME(self) -> str:
        return datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")

    # API Settings
    API_TITLE: str = "Web Scraper API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Task Settings
    TASK_CLEANUP_HOURS: int = 24
    MAX_CONCURRENT_TASKS: int = 5

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
