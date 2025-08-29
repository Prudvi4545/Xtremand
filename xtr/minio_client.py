from minio import Minio
import os


minio_client = Minio(
    "172.16.17.161:9000",  
    access_key="Xtremand",
    secret_key="Xtremand@321",
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



# new


# from minio import Minio
# from minio.error import S3Error

# # -----------------------------
# # MinIO connection parameters
# # -----------------------------
# MINIO_HOST = "172.16.17.161:9000"  # API port, not browser port
# ACCESS_KEY = "Xtremand"
# SECRET_KEY = "Xtremand@321"
# SECURE = False  # True if using HTTPS

# # -----------------------------
# # Initialize MinIO client
# # -----------------------------
# minio_client = Minio(
#     MINIO_HOST,
#     access_key=ACCESS_KEY,
#     secret_key=SECRET_KEY,
#     secure=SECURE
# )

# print("MinIO client initialized successfully.")

# # -----------------------------
# # List all buckets
# # -----------------------------
# try:
#     buckets = minio_client.list_buckets()
#     print("Available Buckets:")
#     for bucket in buckets:
#         print(f" - {bucket.name}")
# except S3Error as e:
#     print(f"Error listing buckets: {e}")

# # -----------------------------
# # Helper function to list objects in a bucket
# # -----------------------------
# def list_objects(bucket_name):
#     """
#     List all objects in the specified bucket recursively.
#     Returns a generator of objects.
#     """
#     try:
#         objects = minio_client.list_objects(bucket_name, recursive=True)
#         return objects
#     except S3Error as e:
#         print(f"Error listing objects in bucket '{bucket_name}': {e}")
#         return []
