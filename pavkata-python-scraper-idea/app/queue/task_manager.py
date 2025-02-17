import logging
from typing import Dict, Optional
from celery import Celery
from datetime import datetime
import asyncio
from functools import wraps

from ..core.config import Config
from ..models.task import TaskResponse, TaskStatus
from ..services.schema_generator import SchemaGenerator
from ..services.content_scraper import ContentScraper
from ..core.exceptions import ScrapingException, MissingContentError, ExtractionError
from crawl4ai import Crawler

logger = logging.getLogger(__name__)

def async_to_sync(f):
    """Decorator to run async functions in celery tasks"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

celery_app = Celery('scraper', broker=Config.REDIS_URL)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=1800,  # 30 minutes soft limit
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=1,  # One task at a time
    task_routes={
        'scraper.process_task': {'queue': 'scraping'}
    }
)

class TaskManager:
    def __init__(self):
        self.crawler = Crawler(api_key=Config.CRAWL4AI_API_KEY)
        self.schema_generator = SchemaGenerator(Config.RULES_DIR, self.crawler)
        self.content_scraper = ContentScraper()
        self.tasks: Dict[str, TaskResponse] = {}
        
        # Initialize task cleanup
        self._setup_task_cleanup()
    
    def _setup_task_cleanup(self):
        """Setup periodic task cleanup"""
        @celery_app.task
        def cleanup_old_tasks():
            current_time = datetime.utcnow()
            to_remove = []
            
            for task_id, task in self.tasks.items():
                # Remove completed/failed tasks older than 24 hours
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    if task.completed_at and (current_time - task.completed_at).hours >= 24:
                        to_remove.append(task_id)
                
                # Remove stuck tasks older than 6 hours
                elif (current_time - task.created_at).hours >= 6:
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                self.tasks.pop(task_id, None)
        
        # Schedule cleanup every hour
        celery_app.add_periodic_task(
            3600.0,  # 1 hour
            cleanup_old_tasks.s(),
            name='cleanup-old-tasks'
        )
    
    @celery_app.task(bind=True, max_retries=3)
    @async_to_sync
    async def process_task(self, task_id: str, url: str,
                          headers: Optional[Dict] = None,
                          timeout: int = 30) -> None:
        """
        Process a scraping task with retries and failsafe mechanisms
        
        Args:
            task_id: Unique identifier for the task
            url: URL to scrape
            headers: Optional request headers
            timeout: Request timeout in seconds
        """
        try:
            # Update task status
            self._update_task_status(task_id, TaskStatus.PROCESSING)
            
            # Get or generate config
            config = await self.schema_generator.load_config(url)
            if not config:
                config = await self.schema_generator.generate_config(url)
                logger.info(f"Generated new config for {url}")
            
            # Update config with request-specific settings
            config = self._update_config_settings(config, headers, timeout)
            
            try:
                # Attempt scraping
                result = await self.content_scraper.scrape(url, config)
                self._update_task_success(task_id, result)
                logger.info(f"Successfully scraped {url}")
                
            except (MissingContentError, ExtractionError) as scrape_error:
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
            logger.error(f"Task processing failed for {url}: {str(e)}")
            self._update_task_failure(task_id, str(e))
            
            # Determine if we should retry
            if self.process_task.request.retries < self.process_task.max_retries:
                # Exponential backoff
                retry_delay = 60 * (2 ** self.process_task.request.retries)
                raise self.process_task.retry(
                    exc=e,
                    countdown=retry_delay,
                    max_retries=3
                )
        
        except Exception as e:
            logger.error(
                f"Unexpected error processing task {task_id} for {url}: {str(e)}",
                exc_info=True
            )
            self._update_task_failure(task_id, f"Internal error: {str(e)}")
    
    def _update_config_settings(self, config: Dict, headers: Optional[Dict],
                              timeout: int) -> Dict:
        """Update configuration with request-specific settings"""
        if headers:
            config['headers'] = {
                **config.get('headers', {}),
                **headers
            }
        
        config['timeout'] = timeout
        return config
    
    def _update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update task status and timestamps"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = status
            task.updated_at = datetime.utcnow()
            logger.debug(f"Updated task {task_id} status to {status}")
    
    def _update_task_success(self, task_id: str, result: Dict) -> None:
        """Update task with successful result"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            task.result = result
            logger.info(f"Task {task_id} completed successfully")
    
    def _update_task_failure(self, task_id: str, error: str) -> None:
        """Update task with failure information"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            task.error = error
            logger.error(f"Task {task_id} failed: {error}")