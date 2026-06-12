"""
IWASMS URL Configuration
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/events/', include('apps.events.urls')),
    path('api/v1/alerts/', include('apps.alerts.urls')),
    path('api/v1/models/', include('apps.ml.urls')),
    path('api/v1/stats/', include('apps.dashboard.urls')),
    # Top-level classify endpoint (Section 3.8.2)
    path('api/v1/classify/', include('apps.events.classify_urls')),
]
