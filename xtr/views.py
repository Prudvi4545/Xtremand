import json
from celery import shared_task
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse

from .tasks import auto_discover_and_process  # ✅ Only import this
from .models import HtmlFile

def start_auto_processing(request):
    from .tasks import fetch_all_buckets_and_objects
    fetch_all_buckets_and_objects.delay()
    return JsonResponse({'status': 'processing started'})

def process_files_from_minio(request):
    auto_discover_and_process.delay()
    return HttpResponse("Task triggered!")

def home(request):
    return HttpResponse("<h2>Welcome! 🎉</h2><p>Go to <a href='/process/'>/process/</a> to start the task.</p>")

@shared_task
def process_file_from_minio(event_data):
    # Extract bucket + object info
    bucket = event_data["Records"][0]["s3"]["bucket"]["name"]
    file_name = event_data["Records"][0]["s3"]["object"]["key"]

    # TODO: Add your MinIO fetch + cleaning + MongoDB insert logic here
    print(f"Processing file {file_name} from bucket {bucket}")

def minio_event_webhook(request):
    if request.method == "POST":
        event_data = json.loads(request.body.decode("utf-8"))
        # Call Celery task asynchronously
        process_file_from_minio.delay(event_data)
        return JsonResponse({"status": "received"}, status=200)
    return JsonResponse({"error": "Invalid request"}, status=400)