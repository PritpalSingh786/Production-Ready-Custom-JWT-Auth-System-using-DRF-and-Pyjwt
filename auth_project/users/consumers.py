import json
from channels.generic.websocket import AsyncWebsocketConsumer
from users.utils import averify_token  # ← async version


class AuthConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope["query_string"].decode()
        token = None
        
        if "token=" in query_string:
            token = query_string.split("token=")[1].split("&")[0]
        
        user_id = None
        device_id = None
        
        if token:
            payload = await averify_token(token, 'access')  # ← await use karo
            if payload:
                user_id = payload.get('user_id')
                device_id = payload.get('device_id')
        
        if not user_id or not device_id:
            await self.close()
            return
        
        self.user_id = user_id
        self.device_id = device_id
        self.group_name = f"user_{user_id}_{device_id}"
        
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