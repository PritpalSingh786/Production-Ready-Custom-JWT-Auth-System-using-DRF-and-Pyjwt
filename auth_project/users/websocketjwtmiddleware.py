import jwt

from django.conf import settings
from django.contrib.auth.models import (
    AnonymousUser
)

from channels.middleware import BaseMiddleware

from asgiref.sync import sync_to_async

from users.models import User


class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(
        self,
        scope,
        receive,
        send
    ):
        query_string = scope[
            "query_string"
        ].decode()

        token = None

        if "token=" in query_string:
            token = (
                query_string
                .split("token=")[1]
                .split("&")[0]
            )

        scope["user"] = AnonymousUser()

        if token:

            try:
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[
                        settings.JWT_ALGORITHM
                    ],
                    audience=settings.JWT_AUDIENCE,
                    issuer=settings.JWT_ISSUER
                )

                user = await sync_to_async(
                    User.objects.get
                )(
                    id=payload["user_id"]
                )

                scope["user"] = user

                scope["device_id"] = payload.get(
                    "device_id"
                )

                scope["platform"] = payload.get(
                    "platform"
                )

            except jwt.ExpiredSignatureError:

                await send({
                    "type": "websocket.close",
                    "code": 4001
                })

                return

            except jwt.InvalidTokenError:

                await send({
                    "type": "websocket.close",
                    "code": 4001
                })

                return

            except User.DoesNotExist:

                await send({
                    "type": "websocket.close",
                    "code": 4001
                })

                return

        return await super().__call__(
            scope,
            receive,
            send
        )