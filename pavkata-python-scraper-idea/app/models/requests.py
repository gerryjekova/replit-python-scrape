from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict

class ScrapeRequest(BaseModel):
    url: HttpUrl
    headers: Optional[Dict[str, str]] = None
    options: Optional[Dict[str, any]] = Field(
        default_factory=lambda: {
            "max_retries": 3,
            "timeout": 30,
            "use_javascript": False
        }
    )

class ConfigGenerateRequest(BaseModel):
    url: HttpUrl
    force: bool = False