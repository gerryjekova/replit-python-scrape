import json
import os
from urllib.parse import urlparse
from typing import Optional
import logging
from crawl4ai import Crawler
from ..models.domain_config import DomainConfig, ExtractionRule, MediaExtraction, SelectorType

logger = logging.getLogger(__name__)

class SchemaGenerator:
    def __init__(self, config_dir: str, crawler: Crawler):
        self.config_dir = config_dir
        self.crawler = crawler
        os.makedirs(config_dir, exist_ok=True)
    
    def _get_config_path(self, domain: str) -> str:
        return os.path.join(self.config_dir, f"{domain}.json")
    
    def load_config(self, url: str) -> Optional[DomainConfig]:
        """Load domain configuration if it exists"""
        domain = urlparse(url).netloc
        config_path = self._get_config_path(domain)
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                return self._parse_config(data)
            except Exception as e:
                logger.error(f"Error loading config for {domain}: {str(e)}")
                return None
        return None
    
    def _parse_config(self, data: dict) -> DomainConfig:
        """Parse JSON config into DomainConfig object"""
        extraction_rules = {
            field: ExtractionRule(
                selector=rule["selector"],
                selector_type=SelectorType(rule["selector_type"]),
                attribute=rule.get("attribute"),
                post_process=rule.get("post_process")
            )
            for field, rule in data["extraction_rules"].items()
        }
        
        media_rules = MediaExtraction(
            images=ExtractionRule(**data["media_rules"]["images"]),
            videos=ExtractionRule(**data["media_rules"]["videos"]),
            embeds=ExtractionRule(**data["media_rules"]["embeds"])
        )
        
        return DomainConfig(
            domain=data["domain"],
            use_headless=data.get("use_headless", False),
            use_proxy=data.get("use_proxy", False),
            timeout=data.get("timeout", 30),
            user_agent=data.get("user_agent"),
            proxy_config=data.get("proxy_config"),
            retry_count=data.get("retry_count", 3),
            extraction_rules=extraction_rules,
            media_rules=media_rules
        )
    
    async def generate_config(self, url: str) -> DomainConfig:
        """Generate new configuration using Crawl4AI's LLM capabilities"""
        domain = urlparse(url).netloc
        logger.info(f"Generating new config for domain: {domain}")
        
        try:
            # Use Crawl4AI to analyze the page and generate schema
            schema = await self.crawler.analyze_page(
                url,
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
            
            # Convert Crawl4AI schema to our config format
            config = self._convert_schema_to_config(domain, schema)
            
            # Save the config
            config_path = self._get_config_path(domain)
            with open(config_path, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            
            return config
            
        except Exception as e:
            logger.error(f"Error generating config for {domain}: {str(e)}")
            raise
    
    def _convert_schema_to_config(self, domain: str, schema: dict) -> DomainConfig:
        """Convert Crawl4AI schema to DomainConfig"""
        extraction_rules = {}
        for field, rule in schema.items():
            if field not in ["images", "videos", "embeds"]:
                extraction_rules[field] = ExtractionRule(
                    selector=rule["selector"],
                    selector_type=SelectorType(rule["selector_type"]),
                    attribute=rule.get("attribute"),
                    post_process=rule.get("post_process")
                )
        
        media_rules = MediaExtraction(
            images=ExtractionRule(**schema["images"]),
            videos=ExtractionRule(**schema["videos"]),
            embeds=ExtractionRule(**schema["embeds"])
        )
        
        return DomainConfig(
            domain=domain,
            extraction_rules=extraction_rules,
            media_rules=media_rules
        )