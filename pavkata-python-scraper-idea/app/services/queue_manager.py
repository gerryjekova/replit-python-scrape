from crawl4ai import Crawler
from crawl4ai.config import BrowserConfig, CrawlerRunConfig


class QueueManager:

    def __init__(self):
        """Initialize QueueManager with required services"""
        # Basic browser configuration
        browser_config = BrowserConfig(
            headless=True,  # Run in headless mode
            timeout=30  # Default timeout in seconds
        )

        # Initialize crawler without API key
        self.crawler = Crawler(browser_config=browser_config)
        self.schema_generator = SchemaGenerator(Config.RULES_DIR)
        self.content_scraper = ContentScraper()
        self.tasks = {}
