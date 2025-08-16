from celery.schedules import crontab
import os
from celery import Celery
import django  # ✅ Import this

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_project.settings')

django.setup()  # ✅ Call this before creating Celery app

app = Celery('web_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic task schedule (must be after app is defined)
app.conf.beat_schedule = {
    'auto-process-every-5-min': {
        'task': 'xtr.tasks.fetch_all_buckets_and_objects',
        'schedule': crontab(minute='*/1'),
    },
}
app.conf.timezone = 'UTC'
import os
from celery import Celery
import django  # ✅ Import this

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_project.settings')

django.setup()  # ✅ Call this before creating Celery app

app = Celery('web_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
