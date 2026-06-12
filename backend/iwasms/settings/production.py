import os
from .base import *

DEBUG = False

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split()

# Database — use DATABASE_URL from Render/Railway
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL, conn_max_age=600, ssl_require=True
        )
    }

# Auto-create admin user (set these env vars on Render)
ADMIN_USERNAME = os.environ.get('DJANGO_ADMIN_USERNAME', 'admin')
ADMIN_EMAIL = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@iwasms.local')
ADMIN_PASSWORD = os.environ.get('DJANGO_ADMIN_PASSWORD', 'admin123')

# Redis — use REDIS_URL from Render/Railway
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# CORS — allow your Netlify frontend
CORS_ALLOWED_ORIGINS = [
    origin.strip().rstrip('/') for origin in
    os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

# Security
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
