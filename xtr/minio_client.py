# minio_client.py
import os
from minio import Minio
from minio.error import S3Error

# -----------------------------
# Check environment (local or server)
# -----------------------------
DB_ENV = os.environ.get("DJANGO_DB_ENV", "local")

# -----------------------------
# MinIO Config for local & server
# -----------------------------
if DB_ENV == "server":
    MINIO_HOST = os.environ.get("MINIO_HOST", "172.16.17.161:9000")
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "Xtremand")
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "Xtremand@321")
    MINIO_SECURE = os.environ.get("MINIO_SECURE", "False").lower() == "true"
else:  # local
    MINIO_HOST = os.environ.get("MINIO_HOST", "localhost:9000")
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE = os.environ.get("MINIO_SECURE", "False").lower() == "true"

# -----------------------------
# Initialize MinIO client
# -----------------------------
minio_client = Minio(
    MINIO_HOST,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)

print(f"✅ MinIO client initialized for [{DB_ENV}] environment: {MINIO_HOST}")


# -----------------------------
# Helper function to list objects
# -----------------------------
def list_objects(bucket_name: str):
    """
    List all objects in the specified bucket recursively.
    Returns a generator of objects.
    """
    try:
        return minio_client.list_objects(bucket_name, recursive=True)
    except S3Error as e:
        print(f"❌ Error listing objects in bucket '{bucket_name}': {e}")
        return []
