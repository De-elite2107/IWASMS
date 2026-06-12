"""
IWASMS Django init — ensure Celery app is loaded.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
