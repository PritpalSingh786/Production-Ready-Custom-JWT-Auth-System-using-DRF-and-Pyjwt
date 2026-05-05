import json
from channels.generic.websocket import AsyncWebsocketConsumer


class AuthConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        device_id = self.scope.get("device_id")

        if user.is_anonymous or not device_id:
            await self.close()
            return

        self.group_name = f"user_{user.id}_{device_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        await self.send(text_data=json.dumps({
            "type": "CONNECTED",
            "message": "WebSocket connected successfully"
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def session_killed(self, event):
        await self.send(text_data=json.dumps({
            "type": "SESSION_KILLED",
            "message": event.get("message", "Your session has been terminated")
        }))