"""
IWASMS Test Settings
Inherits from development but swaps Postgres→SQLite and Redis→InMemory.
"""
from .development import *  # noqa

# ── Database: SQLite in-memory (no Postgres needed) ──────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# ── Channel Layer: in-memory (no Redis needed) ────────────────────────────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ── Celery: run tasks inline during tests ────────────────────────────────────
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ── Static files: skip compression ──────────────────────────────────────────
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ── Suppress migration noise in test output ──────────────────────────────────
# SQLite auto-creates tables from models, but we still run migrations normally.
# (No need to suppress — SQLite in-memory runs very fast.)
