from typing import Optional, Dict
import aiohttp
import logging
from urllib.parse import urlparse
from ..core.exceptions import ConnectionError

logger = logging.getLogger(__name__)

async def validate_url(url: str) -> bool:
    """Validate URL accessibility"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=True) as response:
                return response.status < 400
    except Exception as e:
        logger.error(f"URL validation failed for {url}: {str(e)}")
        raise ConnectionError(f"Failed to connect to {url}")

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    return urlparse(url).netloc

def merge_headers(default_headers: Optional[Dict] = None,
                 custom_headers: Optional[Dict] = None) -> Dict:
    """Merge default and custom headers"""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ScraperBot/1.0;)"
    }
    
    if default_headers:
        headers.update(default_headers)
    
    if custom_headers:
        headers.update(custom_headers)
    
    return headers