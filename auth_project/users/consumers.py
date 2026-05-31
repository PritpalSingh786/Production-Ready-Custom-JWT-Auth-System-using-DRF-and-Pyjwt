import json

from channels.generic.websocket import (
    AsyncWebsocketConsumer
)


class AuthConsumer(
    AsyncWebsocketConsumer
):

    async def connect(self):

        user = self.scope["user"]

        if not getattr(
            user,
            "is_authenticated",
            False
        ):
            await self.close(
                code=4001
            )
            return

        self.user_id = str(
            user.id
        )

        self.device_id = (
            self.scope.get(
                "device_id"
            )
        )

        if not self.device_id:
            await self.close(
                code=4001
            )
            return

        self.group_name = (
            f"user_{self.user_id}_"
            f"{self.device_id}"
        )

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        await self.send(
            text_data=json.dumps({
                "type": "CONNECTED",
                "message": (
                    "WebSocket connected successfully"
                )
            })
        )

    async def disconnect(
        self,
        close_code
    ):
        if hasattr(
            self,
            "group_name"
        ):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def logout_notification(
        self,
        event
    ):
        await self.send(
            text_data=json.dumps({
                "type": "LOGOUT",
                "message": event[
                    "message"
                ],
                "action":
                "redirect_login"
            })
        )