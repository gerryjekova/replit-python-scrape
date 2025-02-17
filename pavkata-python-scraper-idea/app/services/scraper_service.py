from typing import Dict, Optional
import logging
from crawl4ai import Crawler
from ..models.domain_config import DomainConfig
from ..models.scraping import ScrapedContent
from ..services.config_service import ConfigService
from ..core.config import settings

logger = logging.getLogger(__name__)

class ScraperService:
    def __init__(self, config_service: ConfigService):
        self.crawler = Crawler(api_key=settings.CRAWL4AI_API_KEY)
        self.config_service = config_service
    
    async def scrape(self, url: str, headers: Optional[Dict] = None,
                    options: Optional[Dict] = None) -> Dict:
        """
        Scrape content using Crawl4AI with domain configuration
        """
        try:
            # Get or generate domain configuration
            config = await self.config_service.get_config(url)
            if not config:
                config = await self._generate_config(url)
                await self.config_service.save_config(url, config)
            
            # Apply request-specific settings
            config = self._apply_request_settings(config, headers, options)
            
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
            # Analyze page structure
            schema = await self.crawler.analyze_page(
                url=url,
                fields=[
                    "title",
                    "content",
                    "author",
                    "publish_date",
                    "language",
                    "categories",
                    "images",
                    "videos",
                    "embeds"
                ]
            )
            
            # Convert schema to our config format
            config = DomainConfig(
                selectors=schema.get('selectors', {}),
                use_javascript=schema.get('requires_javascript', False),
                timeout=settings.SCRAPE_TIMEOUT,
                retry_count=settings.MAX_RETRIES
            )
            
            return config
            
        except Exception as e:
            logger.error(f"Config generation failed for {url}: {str(e)}")
            raise
    
    def _apply_request_settings(self, config: DomainConfig,
                              headers: Optional[Dict],
                              options: Optional[Dict]) -> DomainConfig:
        """Apply request-specific settings to configuration"""
        if headers:
            config.headers = headers
        
        if options:
            config.timeout = options.get('timeout', config.timeout)
            config.use_javascript = options.get('use_javascript',
                                             config.use_javascript)
        
        return config
    
    async def _extract_content(self, url: str, config: DomainConfig) -> ScrapedContent:
        """Extract content using configuration"""
        try:
            # Use Crawl4AI with our configuration
            result = await self.crawler.extract(
                url=url,
                selectors=config.selectors,
                javascript=config.use_javascript,
                timeout=config.timeout
            )
            
            # Convert to our format
            return ScrapedContent(
                title=result.get('title'),
                content=result.get('content'),
                author=result.get('author'),
                publish_date=result.get('publish_date'),
                language=result.get('language'),
                categories=result.get('categories', []),
                media_files={
                    'images': result.get('images', []),
                    'videos': result.get('videos', []),
                    'embeds': result.get('embeds', [])
                }
            )
            
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {str(e)}")
            raise