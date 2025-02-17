import os

class Config:
    # Queue Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Storage Configuration
    RULES_DIR = os.path.join(os.path.dirname(__file__), 'rules/domains')
    
    # Retry Configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 60  # seconds
    
    # Crawl4AI Configuration
    CRAWL4AI_API_KEY = os.getenv('CRAWL4AI_API_KEY')