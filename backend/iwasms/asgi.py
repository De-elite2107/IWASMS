"""
IWASMS ASGI Configuration
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iwasms.settings.development')

django_asgi_app = get_asgi_application()

from apps.events.consumers import SecurityEventConsumer

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws/events/', SecurityEventConsumer.as_asgi()),
        ])
    ),
})
