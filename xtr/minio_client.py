# xtr/minio_client.py

import os
import logging
from minio import Minio
from minio.commonconfig import CopySource

logger = logging.getLogger(__name__)

# -----------------------------
# Environment
# -----------------------------
DB_ENV = os.getenv("DJANGO_DB_ENV", "local")

if DB_ENV == "server":
    MINIO_HOST = os.getenv("MINIO_HOST", "127.0.0.1:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "Xtremand")
    MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "Xtremand@321")
    MINIO_SECURE = False
else:
    MINIO_HOST = "localhost:9000"
    MINIO_ACCESS_KEY = "minioadmin"
    MINIO_SECRET_KEY = "minioadmin"
    MINIO_SECURE = False

# -----------------------------
# Singleton MinIO client
# -----------------------------
_CLIENT = None

def get_minio_client() -> Minio:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = Minio(
            MINIO_HOST,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
        )
        logger.info("✅ MinIO connected: %s", MINIO_HOST)
    return _CLIENT


def list_objects(bucket_name, recursive=True):
    client = get_minio_client()
    return client.list_objects(bucket_name, recursive=recursive)


def move_object(source_bucket: str, object_name: str, dest_bucket: str) -> bool:
    """
    Copy object to dest bucket and delete from source bucket
    """
    try:
        client = get_minio_client()
        src = CopySource(source_bucket, object_name)
        client.copy_object(dest_bucket, object_name, src)
        client.remove_object(source_bucket, object_name)
        logger.info("📦 Moved %s: %s → %s", object_name, source_bucket, dest_bucket)
        return True
    except Exception as e:
        logger.error("❌ Failed to move %s: %s", object_name, e)
        return False
