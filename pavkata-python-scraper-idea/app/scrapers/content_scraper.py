from typing import Dict, Optional
import logging
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from ..models.domain_config import DomainConfig, SelectorType
from ..models.scraped_content import ScrapedContent

logger = logging.getLogger(__name__)

class ContentScraper:
    def __init__(self):
        self.session = requests.Session()
    
    def _get_headless_browser(self) -> webdriver.Chrome:
        """Initialize headless Chrome browser"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=chrome_options)
    
    def _extract_with_selector(self, soup: BeautifulSoup, rule: dict) -> Optional[str]:
        """Extract content using specified selector"""
        try:
            if rule.selector_type == SelectorType.CSS:
                elements = soup.select(rule.selector)
            else:  # XPath
                elements = soup.find_all(xpath=rule.selector)
            
            if not elements:
                logger.warning(f"No elements found for selector {rule.selector}")
                return None

            element = elements[0]
            if element is None:
                logger.warning("First element is None")
                return None

            if rule.attribute:
                return element.get(rule.attribute)

            try:
                return element.get_text(strip=True)
            except AttributeError:
                logger.warning(f"Could not extract text from element: {element}")
                return None
            
        except Exception as e:
            logger.error(f"Error extracting with selector {rule.selector}: {str(e)}")
            return None
    
    def scrape(self, url: str, config: DomainConfig) -> ScrapedContent:
        """Scrape content using provided configuration"""
        try:
            # Setup session with custom user agent if specified
            if config.user_agent:
                self.session.headers.update({"User-Agent": config.user_agent})
            
            # Get page content
            if config.use_headless:
                driver = self._get_headless_browser()
                driver.get(url)
                html = driver.page_source
                driver.quit()
            else:
                response = self.session.get(
                    url,
                    timeout=config.timeout,
                    proxies=config.proxy_config if config.use_proxy else None
                )
                html = response.text
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract content using rules
            content = {}
            for field, rule in config.extraction_rules.items():
                content[field] = self._extract_with_selector(soup, rule)
            
            # Extract media
            media_files = {
                "images": self._extract_media(soup, config.media_rules.images),
                "videos": self._extract_media(soup, config.media_rules.videos),
                "embeds": self._extract_media(soup, config.media_rules.embeds)
            }
            
            return ScrapedContent(
                title=content.get("title"),
                content=content.get("content"),
                author=content.get("author"),
                publish_date=content.get("publish_date"),
                language=content.get("language"),
                categories=content.get("categories", []),
                media_files=media_files
            )
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            raise
    
    def _extract_media(self, soup: BeautifulSoup, rule: dict) -> list:
        """Extract media elements using specified rule"""
        try:
            if rule.selector_type == SelectorType.CSS:
                elements = soup.select(rule.selector)
            else:  # XPath
                elements = soup.find_all(xpath=rule.selector)
            
            urls = []
            for element in elements:
                if rule.attribute:
                    url = element.get(rule.attribute)
                    if url:
                        urls.append(url)
            
            return urls
            
        except Exception as e:
            logger.error(f"Error extracting media: {str(e)}")
            return []