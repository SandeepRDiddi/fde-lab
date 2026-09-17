from celery import Celery

from app.config import settings

celery_app = Celery(
    "fde_lab",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)
celery_app.conf.task_default_queue = "fde_lab"
celery_app.conf.timezone = "UTC"
