from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

class TaskStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ScrapedContent:
    title: str
    content: str
    author: Optional[str]
    publish_date: Optional[str]
    language: Optional[str]
    categories: list
    media_files: Dict[str, list]

@dataclass
class TaskResponse:
    task_id: str
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[ScrapedContent] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "result": self.result.__dict__ if self.result else None
        }