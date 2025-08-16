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
