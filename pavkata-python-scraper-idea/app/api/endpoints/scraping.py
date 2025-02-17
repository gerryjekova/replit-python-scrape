from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
import logging
from crawl4ai import Crawler
from crawl4ai.config import BrowserConfig, CrawlerRunConfig

router = APIRouter()
logger = logging.getLogger(__name__)


class ScrapeRequest(BaseModel):
    url: HttpUrl
    max_pages: Optional[int] = 1


@router.post("/scrape")
async def scrape_url(request: Request, scrape_request: ScrapeRequest):
    try:
        # Initialize crawler
        crawler = Crawler(browser_config=BrowserConfig(headless=True))

        # Configure crawler
        run_config = CrawlerRunConfig(url=str(scrape_request.url),
                                      max_pages=scrape_request.max_pages)

        # Run crawler
        result = crawler.run(run_config)

        # Store result
        task_id = f"task_{datetime.utcnow().timestamp()}"
        await request.app.state.storage.store_task(
            task_id, {
                "url": str(scrape_request.url),
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })

        return {
            "task_id": task_id,
            "status": "success",
            "url": str(scrape_request.url),
            "result": result
        }

    except Exception as e:
        logger.error(f"Scraping error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
