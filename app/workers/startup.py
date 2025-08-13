import os
import logging
import asyncio
from typing import Optional

from app.core.database import db_manager, get_db
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def initialize_worker():
    """Initialize worker resources"""
    try:
        # Initialize database connection
        await db_manager.initialize()
        logger.info("Worker database connection initialized")
        
        # Add any other initialization logic here
        # For example: cache warming, loading configuration, etc.
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize worker: {e}")
        return False


async def cleanup_worker():
    """Cleanup worker resources"""
    try:
        # Close database connections
        await db_manager.close()
        logger.info("Worker cleanup completed")
    except Exception as e:
        logger.error(f"Error during worker cleanup: {e}")


@celery_app.task(bind=True)
def worker_init(self):
    """Task to initialize worker on startup"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(initialize_worker())
        if not result:
            raise Exception("Worker initialization failed")
        return "Worker initialized successfully"
    finally:
        loop.close()


@celery_app.task(bind=True)
def worker_cleanup(self):
    """Task to cleanup worker resources"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(cleanup_worker())
        return "Worker cleanup completed"
    finally:
        loop.close()


# Celery signals
@celery_app.signals.worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Called when worker is ready"""
    logger.info(f"Worker {sender} is ready")
    # Run initialization task
    worker_init.delay()


@celery_app.signals.worker_shutdown.connect
def on_worker_shutdown(sender, **kwargs):
    """Called when worker is shutting down"""
    logger.info(f"Worker {sender} is shutting down")
    # Run cleanup task
    worker_cleanup.delay()