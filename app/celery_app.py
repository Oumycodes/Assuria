"""
Celery application configuration.
This is a separate file to avoid circular imports.
For MVP, Celery is optional - workers can run synchronously.
"""

from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Try to import Celery (optional)
try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not available - workers will run synchronously")

# Check if we should use Celery or sync mode
USE_CELERY = (
    CELERY_AVAILABLE and 
    not settings.use_memory_db and 
    settings.redis_url.startswith("redis://")
)

if USE_CELERY:
    try:
        # Create Celery app
        celery_app = Celery(
            "assura_workers",
            broker=settings.redis_url,
            backend=settings.redis_url
        )
        
        # Celery configuration
        celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=30 * 60,  # 30 minutes
            task_soft_time_limit=25 * 60,  # 25 minutes
        )
        
        # Auto-discover tasks
        celery_app.autodiscover_tasks(['app.workers'])
        
        logger.info("Celery configured")
    except Exception as e:
        logger.warning(f"Celery initialization failed, using sync mode: {e}")
        USE_CELERY = False
        celery_app = None
else:
    if not CELERY_AVAILABLE:
        logger.info("Using synchronous processing (Celery not installed)")
    else:
        logger.info("Using synchronous processing (MVP mode)")
    celery_app = None
