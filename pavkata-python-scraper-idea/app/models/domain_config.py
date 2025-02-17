from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class SelectorType(Enum):
    XPATH = "xpath"
    CSS = "css"

@dataclass
class ExtractionRule:
    selector: str
    selector_type: SelectorType
    attribute: Optional[str] = None
    post_process: Optional[str] = None

@dataclass
class MediaExtraction:
    images: ExtractionRule
    videos: ExtractionRule
    embeds: ExtractionRule

@dataclass
class DomainConfig:
    domain: str
    use_headless: bool = False
    use_proxy: bool = False
    timeout: int = 30
    user_agent: Optional[str] = None
    proxy_config: Optional[Dict] = None
    retry_count: int = 3
    extraction_rules: Dict[str, ExtractionRule]
    media_rules: MediaExtraction
    
    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "use_headless": self.use_headless,
            "use_proxy": self.use_proxy,
            "timeout": self.timeout,
            "user_agent": self.user_agent,
            "proxy_config": self.proxy_config,
            "retry_count": self.retry_count,
            "extraction_rules": {
                k: {
                    "selector": v.selector,
                    "selector_type": v.selector_type.value,
                    "attribute": v.attribute,
                    "post_process": v.post_process
                } for k, v in self.extraction_rules.items()
            },
            "media_rules": {
                "images": {
                    "selector": self.media_rules.images.selector,
                    "selector_type": self.media_rules.images.selector_type.value,
                    "attribute": self.media_rules.images.attribute
                },
                "videos": {
                    "selector": self.media_rules.videos.selector,
                    "selector_type": self.media_rules.videos.selector_type.value,
                    "attribute": self.media_rules.videos.attribute
                },
                "embeds": {
                    "selector": self.media_rules.embeds.selector,
                    "selector_type": self.media_rules.embeds.selector_type.value,
                    "attribute": self.media_rules.embeds.attribute
                }
            }
        }