import os

from celery import Celery
from celery.schedules import crontab
import tasks

celery_app = Celery(
    "worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["src.tasks.notifications"]
)

celery_app.conf.timezone = "Europe/Kiev"
