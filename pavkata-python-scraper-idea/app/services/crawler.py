from typing import Dict, Optional
import logging
from urllib.parse import urlparse
from crawl4ai import Crawler
from ..models.scraping import ScrapedContent
from ..models.domain import DomainConfig
from .storage import Storage

logger = logging.getLogger(__name__)

class CrawlerService:
    def __init__(self):
        self.crawler = Crawler()
        self.storage = Storage()
    
    async def scrape(self, url: str, headers: Optional[Dict] = None,
                    timeout: int = 30) -> Dict:
        """
        Scrape content using Crawl4AI with domain-specific configuration
        """
        try:
            domain = urlparse(url).netloc
            
            # Get or generate domain configuration
            config = await self.storage.get_domain_config(domain)
            if not config:
                config = await self._generate_config(url)
                await self.storage.save_domain_config(config)
            
            # Apply request-specific settings
            if headers:
                config.user_agent = headers.get('User-Agent', config.user_agent)
            config.timeout = timeout
            
            # Extract content
            result = await self._extract_content(url, config)
            
            return result.dict()
            
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {str(e)}")
            raise
    
    async def _generate_config(self, url: str) -> DomainConfig:
        """
        Generate domain configuration using Crawl4AI's LLM capabilities
        """
        try:
            schema = await self.crawler.analyze_page(url)
            # Convert Crawl4AI schema to our configuration format
            # (Implementation details would depend on Crawl4AI's schema format)
            return DomainConfig(...)
            
        except Exception as e:
            logger.error(f"Config generation failed for {url}: {str(e)}")
            raise
    
    async def _extract_content(self, url: str, config: DomainConfig) -> ScrapedContent:
        """
        Extract content using domain configuration
        """
        try:
            # Use Crawl4AI with our configuration
            result = await self.crawler.extract(
                url=url,
                rules=config.dict()
            )
            
            return ScrapedContent(**result)
            
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {str(e)}")
            raise