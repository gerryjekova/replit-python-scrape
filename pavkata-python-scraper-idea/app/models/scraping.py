from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, Optional, List, Union
from datetime import datetime

class ScrapedContent(BaseModel):
    title: str
    content: str
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    language: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    media_files: Dict[str, List[str]] = Field(default_factory=dict)

class ScrapeRequest(BaseModel):
    url: HttpUrl
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = Field(default=30, ge=1, le=300)

class ScrapeResponse(BaseModel):
    task_id: str
    status: str = "queued"
    message: str = "Task created successfully"