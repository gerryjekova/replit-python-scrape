from crawl4ai import Crawler
from urllib.parse import urlparse
import json
import os
from config import Config

class SchemaGenerator:
    def __init__(self):
        self.crawler = Crawler(api_key=Config.CRAWL4AI_API_KEY)
    
    def _get_domain_path(self, url):
        domain = urlparse(url).netloc
        return os.path.join(Config.RULES_DIR, f"{domain}.json")
    
    async def generate_schema(self, url):
        """Generate extraction schema using Crawl4AI"""
        try:
            # Use Crawl4AI to analyze the webpage and generate schema
            schema = await self.crawler.generate_schema(url)
            
            # Save the generated schema
            domain_path = self._get_domain_path(url)
            with open(domain_path, 'w') as f:
                json.dump(schema, f, indent=2)
            
            return schema
        except Exception as e:
            raise Exception(f"Schema generation failed: {str(e)}")
    
    def load_schema(self, url):
        """Load existing schema for domain if it exists"""
        domain_path = self._get_domain_path(url)
        if os.path.exists(domain_path):
            with open(domain_path, 'r') as f:
                return json.load(f)
        return None