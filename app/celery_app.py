"""
Celery application configuration.
This is a separate file to avoid circular imports.
"""

from celery import Celery
from app.config import settings

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
