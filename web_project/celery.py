import os
from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
import mongoengine

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_project.settings")

# Create Celery app
app = Celery("web_project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# -----------------------------
# Mongo reconnect logic (fixes "MongoClient opened before fork")
# -----------------------------
def _mongo_config_from_env():
    DB_ENV = os.environ.get("DJANGO_DB_ENV", "local")
    if DB_ENV == "server":
        return {
            "host": os.environ.get("MONGO_HOST", "mongodb://154.210.235.101:27017"),
            "db": os.environ.get("MONGO_DB", "xtremand_qa"),
            "username": os.environ.get("MONGO_USER", "Xtremand"),
            "password": os.environ.get("MONGO_PASS", "Xtremand@321"),
        }
    else:
        return {
            "host": os.environ.get("MONGO_HOST", "mongodb://localhost:27017"),
            "db": os.environ.get("MONGO_DB", "xtremand_qa"),
            "username": os.environ.get("MONGO_USER", "admin"),
            "password": os.environ.get("MONGO_PASS", "StrongAdminPassword123"),
        }

@worker_process_init.connect
def celery_worker_init(**kwargs):
    """Reconnect Mongo safely inside each Celery worker process."""
    try:
        mongoengine.disconnect(alias="default")
    except Exception:
        pass

    cfg = _mongo_config_from_env()
    mongoengine.connect(
        db=cfg["db"],
        host=cfg["host"],
        username=cfg["username"],
        password=cfg["password"],
        authentication_source="admin",
        alias="default",
    )
    print("✅ MongoEngine connected in Celery worker process")

@worker_process_shutdown.connect
def celery_worker_shutdown(**kwargs):
    try:
        mongoengine.disconnect(alias="default")
        print("🛑 MongoEngine disconnected from Celery worker process")
    except Exception:
        pass
