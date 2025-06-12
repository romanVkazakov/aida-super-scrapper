from celery import Celery
import os

# основной объект Celery
celery = Celery(
    "aida",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_BACKEND_URL", "redis://redis:6379/0"),
)

###############################################################################
# Алиасы для совместимости со старыми импортами
###############################################################################
app = celery
celery_app = celery
