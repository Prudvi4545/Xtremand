# web_project/celery.py
import os
from celery import Celery
from celery.schedules import crontab
import django

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_project.settings')

# Setup Django
django.setup()

# Create Celery app
app = Celery('web_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic task schedule
app.conf.beat_schedule = {
    'auto-process-every-1-min': {
        'task': 'xtr.tasks.fetch_all_buckets_and_objects',
        'schedule': crontab(minute='*/1'),  # every 1 minute
    },
}
app.conf.timezone = 'UTC'

# Optional: define a debug task
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')