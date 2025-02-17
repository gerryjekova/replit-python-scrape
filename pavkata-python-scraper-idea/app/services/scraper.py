import logging
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from .models.domain_config import DomainConfig, SelectorType
from .models.scraped_content import ScrapedContent
import requests
import json
import os

logger = logging.getLogger(__name__)

class Scraper:
    """
    Main scraper class that integrates with Crawl4AI and handles
    both API-based and direct HTML scraping methods
    """
    
    def __init__(self, crawl4ai_client=None):
        """
        Initialize scraper with optional Crawl4AI client
        """
        self.session = requests.Session()
        self.crawl4ai_client = crawl4ai_client
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging for the scraper"""
        handler = logging.FileHandler('scraper.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    async def scrape(self, url: str, schema: Dict, headers: Optional[Dict] = None,
                    timeout: int = 30) -> ScrapedContent:
        """
        Main scraping method that handles both Crawl4AI and direct scraping approaches
        """
        try:
            logger.info(f"Starting scraping for URL: {url}")
            
            # Try Crawl4AI first if available
            if self.crawl4ai_client:
                try:
                    return await self._scrape_with_crawl4ai(url, schema)
                except Exception as e:
                    logger.warning(f"Crawl4AI scraping failed, falling back to direct: {str(e)}")
            
            # Fallback to direct scraping
            return await self._scrape_direct(url, schema, headers, timeout)
            
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {str(e)}")
            raise
    
    async def _scrape_with_crawl4ai(self, url: str, schema: Dict) -> ScrapedContent:
        """
        Scrape using Crawl4AI's advanced capabilities
        """
        try:
            # Use Crawl4AI's extraction API
            result = await self.crawl4ai_client.extract(
                url=url,
                schema=schema
            )
            
            # Convert Crawl4AI result to ScrapedContent
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
            logger.error(f"Crawl4AI extraction failed: {str(e)}")
            raise
    
    async def _scrape_direct(self, url: str, schema: Dict, headers: Optional[Dict],
                            timeout: int) -> ScrapedContent:
        """
        Perform direct scraping using BeautifulSoup or Selenium based on schema requirements
        """
        try:
            use_headless = schema.get('use_headless', False)
            html = await self._get_page_content(url, use_headless, headers, timeout)
            
            # Parse the HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract content based on schema
            content = self._extract_content(soup, schema)
            
            # Extract media files
            media_files = self._extract_media_files(soup, schema)
            
            # Create ScrapedContent object
            return ScrapedContent(
                title=content.get('title'),
                content=content.get('content'),
                author=content.get('author'),
                publish_date=content.get('publish_date'),
                language=content.get('language'),
                categories=content.get('categories', []),
                media_files=media_files
            )
            
        except Exception as e:
            logger.error(f"Direct scraping failed: {str(e)}")
            raise
    
    async def _get_page_content(self, url: str, use_headless: bool,
                              headers: Optional[Dict], timeout: int) -> str:
        """
        Get page content using either requests or Selenium
        """
        if use_headless:
            return await self._get_content_with_selenium(url, timeout)
        else:
            return await self._get_content_with_requests(url, headers, timeout)
    
    async def _get_content_with_selenium(self, url: str, timeout: int) -> str:
        """
        Get page content using Selenium for JavaScript-heavy pages
        """
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(timeout)
            
            driver.get(url)
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(("tag name", "body"))
            )
            
            html = driver.page_source
            return html
            
        finally:
            if 'driver' in locals():
                driver.quit()
    
    async def _get_content_with_requests(self, url: str, headers: Optional[Dict],
                                       timeout: int) -> str:
        """
        Get page content using requests for simple pages
        """
        response = self.session.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    
    def _extract_content(self, soup: BeautifulSoup, schema: Dict) -> Dict[str, Any]:
        """
        Extract content based on schema rules
        """
        content = {}
        for field, rules in schema['extraction_rules'].items():
            if isinstance(rules, dict):
                content[field] = self._extract_with_rules(soup, rules)
            else:
                logger.warning(f"Invalid rules format for field {field}")
        return content
    
    def _extract_with_rules(self, soup: BeautifulSoup, rules: Dict) -> Optional[str]:
        """
        Extract content using specified rules
        """
        try:
            selector_type = rules.get('selector_type', 'css')
            selector = rules.get('selector')
            attribute = rules.get('attribute')
            post_process = rules.get('post_process')
            
            if selector_type == 'xpath':
                elements = soup.find_all(xpath=selector)
            else:  # css
                elements = soup.select(selector)
            
            if not elements:
                return None
            
            # Extract content
            element = elements[0]
            content = element.get(attribute) if attribute else element.get_text(strip=True)
            
            # Apply post-processing if specified
            if post_process and content:
                content = self._apply_post_process(content, post_process)
            
            return content
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            return None
    
    def _extract_media_files(self, soup: BeautifulSoup, schema: Dict) -> Dict[str, list]:
        """
        Extract media files based on schema rules
        """
        media_files = {
            'images': [],
            'videos': [],
            'embeds': []
        }
        
        for media_type, rules in schema.get('media_rules', {}).items():
            try:
                if media_type in media_files:
                    urls = self._extract_media_urls(soup, rules)
                    media_files[media_type].extend(urls)
            except Exception as e:
                logger.error(f"Media extraction failed for {media_type}: {str(e)}")
        
        return media_files
    
    def _extract_media_urls(self, soup: BeautifulSoup, rules: Dict) -> list:
        """
        Extract media URLs using specified rules
        """
        urls = []
        try:
            selector_type = rules.get('selector_type', 'css')
            selector = rules.get('selector')
            attribute = rules.get('attribute', 'src')
            
            if selector_type == 'xpath':
                elements = soup.find_all(xpath=selector)
            else:  # css
                elements = soup.select(selector)
            
            for element in elements:
                url = element.get(attribute)
                if url:
                    urls.append(url)
            
            return urls
            
        except Exception as e:
            logger.error(f"Media URL extraction failed: {str(e)}")
            return []
    
    def _apply_post_process(self, content: str, process_type: str) -> str:
        """
        Apply post-processing to extracted content
        """
        if process_type == 'strip':
            return content.strip()
        elif process_type == 'lowercase':
            return content.lower()
        elif process_type == 'uppercase':
            return content.upper()
        # Add more post-processing types as needed
        return content
