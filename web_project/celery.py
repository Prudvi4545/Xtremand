# web_project/celery.py
import os
from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
import mongoengine
from mongoengine.connection import get_connection


# --- Boot Django settings first ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_project.settings")

import django  # noqa: E402
django.setup()  # ensure settings.py runs before tasks/models import

from django.conf import settings  # noqa: E402

# --- Create Celery app ---
app = Celery("web_project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")

# --- Mongo config builder (single source of truth) ---
def _mongo_config():
    db_env = getattr(settings, "DB_ENV", "local")
    if db_env == "server":
        return {
            "host": "mongodb://154.210.235.101:27017",
            "db": "xtremand_qa",
            "username": os.environ.get("MONGO_USERNAME", "Xtremand"),
            "password": os.environ.get("MONGO_PASSWORD", "Xtremand@321"),
            "auth_src": "admin",
        }
    else:
        return {
            "host": "mongodb://localhost:27017",
            "db": "xtremand_qa",
            "username": os.environ.get("MONGO_USERNAME", "admin"),
            "password": os.environ.get("MONGO_PASSWORD", "StrongAdminPassword123"),
            "auth_src": "admin",
        }

logger = app.log.get_default_logger()

# --- Optional: reconnect per worker (safe for prefork) ---
@worker_process_init.connect
def celery_worker_init(**kwargs):
    """Reconnect Mongo safely inside each Celery worker process."""
    try:
        # if a connection exists, close it before forking child
        get_connection(alias="default")
        mongoengine.disconnect(alias="default")
    except Exception:
        pass

    cfg = _mongo_config()

    # Build kwargs without assuming creds are present
    connect_kwargs = dict(
        db=cfg.get("db", "xtremand_qa"),
        host=cfg.get("host", "mongodb://localhost:27017"),
        alias="default",
    )
    if cfg.get("username") and cfg.get("password"):
        connect_kwargs.update(
            username=cfg["username"],
            password=cfg["password"],
            authentication_source=cfg.get("auth_src", "admin"),
        )

    mongoengine.connect(**connect_kwargs)
    logger.info("✅ MongoEngine connected in Celery worker process (env=%s)", getattr(settings, "DB_ENV", "local"))

@worker_process_shutdown.connect
def celery_worker_shutdown(**kwargs):
    """Disconnect Mongo cleanly when Celery worker stops."""
    try:
        mongoengine.disconnect(alias="default")
        logger.warning("🛑 MongoEngine disconnected from Celery worker process")
    except Exception:
        pass
