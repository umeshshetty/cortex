"""
Cortex - Celery Worker Configuration
The "Subconscious" - background tasks that run async.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


# Initialize Celery app
celery_app = Celery(
    "cortex",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.ghost_detection",
        "app.workers.swiss_cheese",
        "app.workers.memory_consolidation",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    worker_prefetch_multiplier=1,
)

# Scheduled tasks (The Sleep Cycle)
celery_app.conf.beat_schedule = {
    # Run every morning at 6:00 AM UTC
    "morning-ghost-check": {
        "task": "app.workers.ghost_detection.detect_ghosts",
        "schedule": crontab(hour=6, minute=0),
    },
    # Run every 4 hours
    "schedule-optimization": {
        "task": "app.workers.swiss_cheese.optimize_schedule",
        "schedule": crontab(minute=0, hour="*/4"),
    },
    # Run nightly at 2:00 AM UTC (Memory consolidation)
    "nightly-consolidation": {
        "task": "app.workers.memory_consolidation.consolidate",
        "schedule": crontab(hour=2, minute=0),
    },
}


# Task decorators for convenience
def background_task(*args, **kwargs):
    """Decorator to register a Celery task."""
    return celery_app.task(*args, **kwargs)
