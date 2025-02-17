import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from ..models.task import TaskStatus, TaskResponse
from ..services.storage import Storage
from ..services.crawler import CrawlerService

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self):
        self.storage = Storage()
        self.crawler = CrawlerService()
        self.tasks: Dict[str, asyncio.Task] = {}
    
    async def create_task(self, url: str, headers: Optional[Dict] = None,
                         timeout: int = 30) -> str:
        """
        Create and queue a new scraping task
        """
        task_id = str(uuid.uuid4())
        
        # Create task metadata
        task_data = TaskResponse(
            task_id=task_id,
            status=TaskStatus.QUEUED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Store task data
        await self.storage.save_task(task_id, task_data)
        
        # Create and store asyncio task
        self.tasks[task_id] = asyncio.create_task(
            self._process_task(task_id, url, headers, timeout)
        )
        
        return task_id
    
    async def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """
        Get task status and result
        """
        return await self.storage.get_task(task_id)
    
    async def _process_task(self, task_id: str, url: str,
                           headers: Optional[Dict], timeout: int):
        """
        Process a scraping task with retries
        """
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Update status to processing
                await self._update_status(task_id, TaskStatus.PROCESSING)
                
                # Attempt scraping
                result = await self.crawler.scrape(url, headers, timeout)
                
                # Update task with success
                await self._update_success(task_id, result)
                return
                
            except Exception as e:
                attempt += 1
                if attempt >= max_attempts:
                    await self._update_failure(task_id, str(e))
                    return
                
                # Wait with exponential backoff before retry
                await asyncio.sleep(60 * (2 ** attempt))
    
    async def _update_status(self, task_id: str, status: TaskStatus):
        """Update task status"""
        task = await self.storage.get_task(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.utcnow()
            await self.storage.save_task(task_id, task)
    
    async def _update_success(self, task_id: str, result: Dict):
        """Update task with successful result"""
        task = await self.storage.get_task(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            task.result = result
            await self.storage.save_task(task_id, task)
    
    async def _update_failure(self, task_id: str, error: str):
        """Update task with failure information"""
        task = await self.storage.get_task(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            task.error = error
            await self.storage.save_task(task_id, task)