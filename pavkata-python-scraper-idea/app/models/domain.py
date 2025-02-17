from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, Optional, List
from enum import Enum

class SelectorType(str, Enum):
    CSS = "css"
    XPATH = "xpath"

class ExtractionRule(BaseModel):
    selector: str
    selector_type: SelectorType = SelectorType.CSS
    attribute: Optional[str] = None
    post_process: Optional[str] = None

class MediaRules(BaseModel):
    images: ExtractionRule
    videos: ExtractionRule
    embeds: ExtractionRule

class DomainConfig(BaseModel):
    domain: str
    use_headless: bool = False
    use_proxy: bool = False
    timeout: int = Field(default=30, ge=1, le=300)
    user_agent: Optional[str] = None
    proxy_config: Optional[Dict] = None
    retry_count: int = Field(default=3, ge=1, le=5)
    extraction_rules: Dict[str, ExtractionRule]
    media_rules: MediaRules