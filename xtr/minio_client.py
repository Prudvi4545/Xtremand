from minio import Minio
import os


minio_client = Minio(
    # "localhost:9000",
    "138.197.202.21:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)
print("MinIO client initialized.")
print(minio_client)

# try:
#     # List all buckets
#     buckets = minio_client.list_buckets()
#     print("Available Buckets:",buckets)
#     print()
#     for bucket in buckets:
#         bucket_name = bucket.name
#         print(f"Bucket: {bucket_name}")
        
#         # List all objects in the current bucket
#         objects = minio_client.list_objects(bucket_name)
#         for obj in objects:
#             print(f" - {obj.object_name}")
            
# except Exception as e:
#     print(f"Error occurred: {e}")

def list_objects(bucket_name):
    return minio_client.list_objects(bucket_name, recursive=True)