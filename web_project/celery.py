import os
from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
import mongoengine
from mongoengine.connection import get_connection
from web_project import settings


DB_ENV = settings.DB_ENV
# -----------------------------
# Django settings
# -----------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_project.settings")

# Create Celery app
app = Celery("web_project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# -----------------------------
# MongoDB connection config
# -----------------------------
def _mongo_config_from_env():
    """
    Return MongoDB connection config depending on environment.
    Uses DJANGO_DB_ENV = "local" or "server".
    """

    if DB_ENV == "server":
        return {
            "host":  "mongodb://154.210.235.101:27017",
            "db": "MONGO_DB", "xtremand_qa"
            "username":  "Xtremand",
            "password": "Xtremand@321",
            "auth_src": "admin",
        }
    else:  # local dev environment
        return {
            "host": "mongodb://localhost:27017",
            "db": "xtremand_qa",
            "username": "admin",
            "password": "StrongAdminPassword123",
            "auth_src": "admin",
        }


# -----------------------------
# Mongo reconnect logic
# -----------------------------
logger = app.log.get_default_logger()

@worker_process_init.connect
def celery_worker_init(**kwargs):
    """Reconnect Mongo safely inside each Celery worker process."""
    try:
        get_connection(alias="default")  # if already connected
        mongoengine.disconnect(alias="default")
    except Exception:
        pass

    cfg = _mongo_config_from_env()
    mongoengine.connect(
        db=cfg["db"],
        host=cfg["host"],
        username=cfg["username"],
        password=cfg["password"],
        authentication_source=cfg["auth_src"],
        alias="default",
    )
    logger.info("✅ MongoEngine connected in Celery worker process (env=%s)", DB_ENV)


@worker_process_shutdown.connect
def celery_worker_shutdown(**kwargs):
    """Disconnect Mongo cleanly when Celery worker stops."""
    try:
        mongoengine.disconnect(alias="default")
        logger.warning("🛑 MongoEngine disconnected from Celery worker process")
    except Exception:
        pass
