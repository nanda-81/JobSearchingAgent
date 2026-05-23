from celery import Celery
from app.core.config import settings

# Initialize Celery app instance using Redis as message broker and backend storage
celery_app = Celery(
    "pjsap_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.jobs"]
)

# Standard queue configuration settings
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour maximum task time
)
