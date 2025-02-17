
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup

class Crawler:
    def __init__(self, browser_config=None):
        self.config = browser_config or {}
        self.session = requests.Session()
        
    def run(self, run_config):
        url = run_config.url
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        return {
            'text': soup.get_text(strip=True),
            'title': soup.title.string if soup.title else '',
            'html': str(soup)
        }

    async def analyze_page(self, url, fields=None):
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return {
            'text': soup.get_text(strip=True),
            'title': soup.title.string if soup.title else ''
        }
