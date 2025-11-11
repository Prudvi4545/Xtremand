"""xtr.minio_client

Centralized MinIO client initializer and small helper wrappers.

Behavior:
- Prefer Django settings if available (import django.conf.settings)
- Fall back to environment variables when Django settings are not present
- Provide helper functions and a safe singleton accessor
"""

import os
import logging
from typing import Iterable

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


def _read_settings_fallback():
    """Return a dict with MinIO configuration.

    Prefer Django settings if they are configured, otherwise use env vars.
    """
    try:
        # Import lazily to avoid import-time side-effects in non-Django contexts
        from django.conf import settings as dj_settings
        cfg = {
            'db_env': getattr(dj_settings, 'DJANGO_DB_ENV', os.environ.get('DJANGO_DB_ENV', 'local')),
            'host': getattr(dj_settings, 'MINIO_HOST', os.environ.get('MINIO_HOST', 'localhost:9000')),
            'access_key': getattr(dj_settings, 'MINIO_ACCESS_KEY', os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')),
            'secret_key': getattr(dj_settings, 'MINIO_SECRET_KEY', os.environ.get('MINIO_SECRET_KEY', 'minioadmin')),
            'secure': getattr(dj_settings, 'MINIO_SECURE', os.environ.get('MINIO_SECURE', 'False').lower() == 'true'),
        }
        return cfg
    except Exception:
        # No Django settings available, fall back to environment
        return {
            'db_env': os.environ.get('DJANGO_DB_ENV', 'local'),
            'host': os.environ.get('MINIO_HOST', 'localhost:9000'),
            'access_key': os.environ.get('MINIO_ACCESS_KEY', 'minioadmin'),
            'secret_key': os.environ.get('MINIO_SECRET_KEY', 'minioadmin'),
            'secure': os.environ.get('MINIO_SECURE', 'False').lower() == 'true',
        }


# module-level singleton
_CLIENT = None


def get_minio_client() -> Minio:
    """Return a singleton Minio client. Initialize on first call.

    Raises RuntimeError on initialization failure.
    """
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    cfg = _read_settings_fallback()
    try:
        client = Minio(
            cfg['host'],
            access_key=cfg['access_key'],
            secret_key=cfg['secret_key'],
            secure=cfg['secure'],
        )
        _CLIENT = client
        logger.info("MinIO client initialized for [%s] at %s", cfg['db_env'], cfg['host'])
        return _CLIENT
    except Exception as exc:
        logger.exception("Failed to initialize MinIO client: %s", exc)
        raise RuntimeError("MinIO client initialization failed") from exc


def list_objects(bucket_name: str) -> Iterable:
    """List objects in a bucket recursively. Returns a generator.

    On error returns an empty list.
    """
    try:
        client = get_minio_client()
        return client.list_objects(bucket_name, recursive=True)
    except S3Error as e:
        logger.error("Error listing objects in bucket '%s': %s", bucket_name, e)
        return []
    except RuntimeError:
        return []


def ensure_bucket_exists(bucket_name: str):
    """Create the bucket if it does not exist.

    Returns True if the bucket exists or was created, False on error.
    """
    try:
        client = get_minio_client()
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info("Created bucket: %s", bucket_name)
        return True
    except Exception as e:
        logger.error("Failed to ensure bucket '%s' exists: %s", bucket_name, e)
        return False


def move_object(source_bucket: str, object_name: str, dest_bucket: str) -> bool:
    """Copy object to dest_bucket and remove original. Returns True on success."""
    try:
        client = get_minio_client()
        from minio.commonconfig import CopySource

        src = CopySource(source_bucket, object_name)
        client.copy_object(dest_bucket, object_name, src)
        client.remove_object(source_bucket, object_name)
        logger.info("Moved '%s' from '%s' to '%s'", object_name, source_bucket, dest_bucket)
        return True
    except Exception as e:
        logger.error("Failed moving object '%s' from '%s' to '%s': %s", object_name, source_bucket, dest_bucket, e)
        return False


def fget_object(bucket_name: str, object_name: str, file_path: str):
    """Download an object to local path. Wrapper for client's fget_object."""
    client = get_minio_client()
    return client.fget_object(bucket_name, object_name, file_path)


# Backwards-compatible top-level alias used in older modules
try:
    # initialize eagerly (keeps behavior similar to previous code)
    get_minio_client()
except Exception:
    # If initialization fails (e.g., missing env in CI), don't crash import time.
    _CLIENT = None
finally:
    # Provide a backwards-compatible symbol `minio_client` used throughout the repo.
    try:
        minio_client = _CLIENT or get_minio_client()
    except Exception:
        # keep it defined to avoid ImportError; callers must handle None
        minio_client = None
