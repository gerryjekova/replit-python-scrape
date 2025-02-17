import logging
from typing import Dict, Optional, Any
from celery import Celery
from datetime import datetime, timedelta
from functools import wraps
import asyncio
import uuid
from crawl4ai import Crawler

from ..core.config import Config
from ..models.task_response import TaskResponse, TaskStatus
from ..scrapers.schema_generator import SchemaGenerator
from ..scrapers.content_scraper import ContentScraper
from ..core.exceptions import (
    ScrapingException,
    ConfigGenerationError,
    ContentExtractionError
)

logger = logging.getLogger(__name__)

def async_to_sync(f):
    """Decorator to handle async functions in Celery tasks"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

# Configure Celery
celery_app = Celery('scraper', broker=Config.REDIS_URL)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=Config.TASK_TIMEOUT,
    worker_prefetch_multiplier=1
)

class QueueManager:
    def __init__(self):
        """Initialize QueueManager with required services"""
        self.crawler = Crawler(api_key=Config.CRAWL4AI_API_KEY)
        self.schema_generator = SchemaGenerator(Config.RULES_DIR, self.crawler)
        self.content_scraper = ContentScraper()
        self.tasks: Dict[str, TaskResponse] = {}
        
        # Setup periodic cleanup
        self._setup_task_cleanup()

    def create_task(self, url: str, headers: Optional[Dict] = None,
                   timeout: int = Config.DEFAULT_TIMEOUT) -> str:
        """Create a new scraping task"""
        task_id = str(uuid.uuid4())
        
        # Initialize task response
        self.tasks[task_id] = TaskResponse(
            task_id=task_id,
            url=url,
            status=TaskStatus.QUEUED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Queue the task
        self.process_task.delay(task_id, url, headers, timeout)
        
        return task_id

    def get_task_status(self, task_id: str) -> Optional[TaskResponse]:
        """Get current task status and result"""
        return self.tasks.get(task_id)

    @celery_app.task(bind=True, max_retries=Config.MAX_RETRIES)
    @async_to_sync
    async def process_task(self, task_id: str, url: str,
                          headers: Optional[Dict] = None,
                          timeout: int = Config.DEFAULT_TIMEOUT) -> None:
        """Process a scraping task with retries and failsafe mechanisms"""
        try:
            # Update task status
            self._update_task_status(task_id, TaskStatus.PROCESSING)
            
            # Get or generate config
            config = await self._get_or_generate_config(url)
            
            # Update config with request-specific settings
            config = self._update_config_settings(config, headers, timeout)
            
            # Attempt scraping
            try:
                result = await self.content_scraper.scrape(url, config)
                self._update_task_success(task_id, result)
                logger.info(f"Successfully scraped {url}")
                
            except ContentExtractionError as scrape_error:
                logger.warning(
                    f"Initial scraping failed for {url}: {str(scrape_error)}. "
                    "Attempting config regeneration..."
                )
                
                # Regenerate config and retry
                config = await self.schema_generator.generate_config(
                    url,
                    force_refresh=True
                )
                config = self._update_config_settings(config, headers, timeout)
                
                try:
                    result = await self.content_scraper.scrape(url, config)
                    self._update_task_success(task_id, result)
                    logger.info(f"Successfully scraped {url} after config regeneration")
                    
                except Exception as retry_error:
                    raise ScrapingException(
                        f"Scraping failed after config regeneration: {str(retry_error)}"
                    )
                
        except ScrapingException as e:
            self._handle_task_error(task_id, str(e), self.process_task)
            
        except Exception as e:
            logger.error(
                f"Unexpected error processing task {task_id}: {str(e)}",
                exc_info=True
            )
            self._update_task_failure(task_id, f"Internal error: {str(e)}")

    async def _get_or_generate_config(self, url: str) -> Dict:
        """Get existing config or generate new one"""
        try:
            config = self.schema_generator.load_config(url)
            if not config:
                config = await self.schema_generator.generate_config(url)
                logger.info(f"Generated new config for {url}")
            return config
            
        except Exception as e:
            raise ConfigGenerationError(f"Failed to get/generate config: {str(e)}")

    def _update_config_settings(self, config: Dict,
                              headers: Optional[Dict],
                              timeout: int) -> Dict:
        """Update configuration with request-specific settings"""
        if headers:
            config['headers'] = {
                **config.get('headers', {}),
                **headers
            }
        config['timeout'] = timeout
        return config

    def _handle_task_error(self, task_id: str, error: str, task: Any) -> None:
        """Handle task error with retry logic"""
        logger.error(f"Task {task_id} failed: {error}")
        self._update_task_failure(task_id, error)
        
        if task.request.retries < task.max_retries:
            retry_delay = Config.RETRY_DELAY * (2 ** task.request.retries)
            raise task.retry(exc=Exception(error), countdown=retry_delay)

    def _update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update task status and timestamp"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.tasks[task_id].updated_at = datetime.utcnow()

    def _update_task_success(self, task_id: str, result: Dict) -> None:
        """Update task with successful result"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
            self.tasks[task_id].completed_at = datetime.utcnow()
            self.tasks[task_id].updated_at = datetime.utcnow()
            self.tasks[task_id].result = result

    def _update_task_failure(self, task_id: str, error: str) -> None:
        """Update task with failure information"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.FAILED
            self.tasks[task_id].completed_at = datetime.utcnow()
            self.tasks[task_id].updated_at = datetime.utcnow()
            self.tasks[task_id].error = error

    def _setup_task_cleanup(self) -> None:
        """Setup periodic task cleanup"""
        @celery_app.task
        def cleanup_old_tasks():
            current_time = datetime.utcnow()
            to_remove = []
            
            for task_id, task in self.tasks.items():
                # Remove completed/failed tasks older than 24 hours
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    if (current_time - task.completed_at) > timedelta(hours=24):
                        to_remove.append(task_id)
                # Remove stuck tasks older than 6 hours
                elif (current_time - task.created_at) > timedelta(hours=6):
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.tasks[task_id]
            
            logger.info(f"Cleaned up {len(to_remove)} old tasks")

        # Schedule cleanup every hour
        celery_app.add_periodic_task(
            3600.0,
            cleanup_old_tasks.s(),
            name='cleanup-old-tasks'
        )