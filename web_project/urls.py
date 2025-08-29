from django.contrib import admin
from django.urls import path
from xtr import views  # ✅ Make sure this matches your app name!
from xtr.views_minio_events import minio_event_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # ✅ Welcome page
    path('process/', views.start_auto_processing, name='process'),  # ✅ Correct task trigger
    path('minio-event/', minio_event_webhook, name='minio_event_webhook'),
]
