from .base import *
import os

DEBUG = True

ALLOWED_HOSTS = ['*']

# PostgreSQL — use localhost when running outside Docker
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'iwasms'),
        'USER': os.environ.get('POSTGRES_USER', 'iwasms'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'iwasms_secret'),
        'HOST': os.environ.get('POSTGRES_HOST', '127.0.0.1'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# Redis on localhost
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(os.environ.get('REDIS_HOST', '127.0.0.1'), 6379)],
        },
    },
}

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/1')

CORS_ALLOW_ALL_ORIGINS = True
