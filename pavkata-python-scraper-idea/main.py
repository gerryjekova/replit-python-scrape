from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone

from .api.endpoints import scraping
from .core.config import settings
from .core.logging import setup_logging
from .core.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware
from .services.storage_service import StorageService
from .services.config_service import ConfigService

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing application services...")
    
    # Initialize storage
    app.state.storage = StorageService(
        storage_type=settings.STORAGE_TYPE,
        redis_url=settings.REDIS_URL
    )
    
    # Initialize config service
    app.state.config_service = ConfigService()
    
    # Start background task cleanup
    if settings.TASK_CLEANUP_HOURS > 0:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            app.state.storage.cleanup_tasks,
            'interval',
            hours=settings.TASK_CLEANUP_HOURS,
            kwargs={'max_age_hours': settings.TASK_CLEANUP_HOURS}
        )
        scheduler.start()
        app.state.scheduler = scheduler
    
    logger.info("Application startup complete")
    yield
    
    # Shutdown
    logger.info("Shutting down application services...")
    
    # Close storage connections
    await app.state.storage.close()
    
    # Stop scheduler if running
    if hasattr(app.state, 'scheduler'):
        app.state.scheduler.shutdown()
    
    logger.info("Shutdown complete")

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Asynchronous web scraping API using Crawl4AI",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    scraping.router,
    prefix="/api/v1",
    tags=["scraping"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.API_VERSION
    }

# Add OpenAPI customization
app.swagger_ui_parameters = {
    "defaultModelsExpandDepth": -1,
    "operationsSorter": "method",
    "tagsSorter": "alpha",
    "persistAuthorization": True,
}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1
    )