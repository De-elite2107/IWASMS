"""
Events WebSocket Consumer
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class SecurityEventConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Validate JWT from query string: ?token=<jwt>
        query_string = self.scope.get('query_string', b'').decode()
        token = None
        for part in query_string.split('&'):
            if part.startswith('token='):
                token = part[6:]
                break

        if token:
            try:
                from rest_framework_simplejwt.tokens import UntypedToken
                from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
                UntypedToken(token)
            except Exception as e:
                logger.warning(f"WS auth failed: {e}")
                await self.close(code=4001)
                return
        else:
            # Allow unauthenticated in development — in prod, reject
            logger.debug("WS connection without token — allowing in dev mode")

        await self.channel_layer.group_add('security_events', self.channel_name)
        await self.accept()
        logger.info(f"WS client connected: {self.channel_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('security_events', self.channel_name)
        logger.info(f"WS client disconnected: {self.channel_name}")

    async def receive(self, text_data):
        # Echo / ping-pong
        pass

    async def security_event(self, event):
        """Handler for messages sent to the 'security_events' group."""
        await self.send(text_data=json.dumps(event['data']))
