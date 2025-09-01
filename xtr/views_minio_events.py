from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .tasks import process_minio_file

def minio_event_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print("Webhook received:", data)   # <--- This will show up in console
        return JsonResponse({"status": "success"})
    return JsonResponse({"error": "invalid method"}, status=405)

# @csrf_exempt
# def minio_event_webhook(request):
#     if request.method == "POST":
#         try:
#             payload = json.loads(request.body.decode())
#             print("[WEBHOOK] MinIO event received:", payload)
#             records = payload.get('Records', [])
#             for record in records:
#                 s3_info = record.get('s3', {})
#                 bucket = s3_info.get('bucket', {}).get('name')
#                 object_key = s3_info.get('object', {}).get('key')
#                 if bucket and object_key:
#                     process_minio_file.delay(bucket, object_key)
#             return JsonResponse({"status": "success"})
#         except Exception as e:
#             print("[WEBHOOK] Error:", e)
#             return JsonResponse({"status": "error", "message": str(e)}, status=400)
#     return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

@csrf_exempt
def minio_event_webhook(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode())
            print("[WEBHOOK] MinIO event received:", payload)
            records = payload.get('Records', [])
            for record in records:
                s3_info = record.get('s3', {})
                bucket = s3_info.get('bucket', {}).get('name')
                object_key = s3_info.get('object', {}).get('key')
                if bucket and object_key:
                    process_minio_file.delay(bucket, object_key)
            return JsonResponse({"status": "success"})
        except Exception as e:
            print("[WEBHOOK] Error:", e)
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)
