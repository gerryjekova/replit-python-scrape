
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class MediaFiles(BaseModel):
    images: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    embeds: List[str] = Field(default_factory=list)

class ScrapingResult(BaseModel):
    title: str
    content: str
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    language: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    media_files: MediaFiles = Field(default_factory=MediaFiles)

class TaskResponse(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user: str
    url: str
    result: Optional[ScrapingResult] = None
    error: Optional[str] = None
