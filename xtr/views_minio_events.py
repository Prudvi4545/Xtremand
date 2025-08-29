from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .tasks import fetch_all_buckets_and_objects

@csrf_exempt
def minio_event_webhook(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode())
            print("[WEBHOOK] MinIO event received:", payload)
            fetch_all_buckets_and_objects.delay()
            return JsonResponse({"status": "success"})
        except Exception as e:
            print("[WEBHOOK] Error:", e)
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)
