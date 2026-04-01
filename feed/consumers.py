import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

User = get_user_model()


async def get_user_from_token(token_key):
    try:
        token = await sync_to_async(Token.objects.select_related('user').get)(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        token_key = None
        query = self.scope.get('query_string', b'').decode('utf-8')
        for part in query.split('&'):
            if part.startswith('token='):
                token_key = part.split('=', 1)[1]
                break

        self.user = await get_user_from_token(token_key) if token_key else None

        if self.user is None:
            await self.close()
            return

        self.group_name = f'user_{self.user.id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Optionally allow clients to request refresh
        if content.get('type') == 'refresh':
            await self.send_json({'type': 'refresh'})

    async def send_notification(self, event):
        notification = event.get('notification')
        if notification is not None:
            await self.send_json({
                'type': 'notification',
                'notification': notification
            })
