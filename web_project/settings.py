import os
from pathlib import Path
import mongoengine

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-w5u4-2g==2lgn+8g4es1u&&m+3$i&gp(ee_s4-!j*a(j$qatz*'

DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'xtr',
]

# ===============================
# Django URL Configuration
# ===============================
ROOT_URLCONF = 'web_project.urls'

# ===============================
# MongoEngine Configuration
# ===============================

DB_ENV = os.environ.get('DJANGO_DB_ENV', 'local')

# Always disconnect existing "default" alias
try:
    mongoengine.disconnect(alias="default")
except Exception:
    pass

if DB_ENV == 'server':
    mongoengine.connect(
        db='xtremand_qa',
        host='mongodb://172.16.17.161:27017',
        username='Xtremand',
        password='Xtremand@321',
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

WSGI_APPLICATION = 'web_project.wsgi.application'

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

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery config
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
