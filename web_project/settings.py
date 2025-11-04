
# ===============================
# Django URL Configuration
# ===============================
import os
from pathlib import Path
import mongoengine
import logging

BASE_DIR = Path(__file__).resolve().parent.parent

ROOT_URLCONF = 'web_project.urls'
WSGI_APPLICATION = 'web_project.wsgi.application'

# ===============================
# Django Secret Key & Debug
# ===============================
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'your-default-insecure-key')
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

# ===============================
# Installed Apps
# ===============================
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'xtr',
]

# ===============================
# MongoEngine Configuration
# ===============================
DB_ENV = os.environ.get('DJANGO_DB_ENV', 'local')
try:
    mongoengine.disconnect(alias="default")
except Exception:
    pass

if DB_ENV == 'server':
    mongoengine.connect(
        db='xtremand_qa',
        host= 'mongodb://154.210.235.101:27017',
        username= 'Xtremand',
        password= 'Xtremand@321',
        authentication_source='admin',
        alias="default"
    )
else:
    mongoengine.connect(
        db='xtremand_qa',
        host='mongodb://localhost:27017',
        username='admin',
        password='StrongAdminPassword123',
        authentication_source='admin',
        alias="default"
    )

# ===============================
# Django + Celery Config
# ===============================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # For collectstatic in production

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===============================
# Celery Configuration
# ===============================
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# ===============================
# Logging Configuration
# ===============================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
