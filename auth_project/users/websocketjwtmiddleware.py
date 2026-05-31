import jwt

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from channels.middleware import BaseMiddleware


class JWTUser:

    def __init__(self, user_id):
        self.id = user_id
        self.user_id = user_id
        self.is_authenticated = True


class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(
        self,
        scope,
        receive,
        send
    ):

        query_string = (
            scope["query_string"]
            .decode()
        )

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

                if (
                    payload.get("type")
                    != "access"
                ):
                    raise jwt.InvalidTokenError(
                        "Invalid token type"
                    )

                scope["user"] = JWTUser(
                    payload["user_id"]
                )

                scope["device_id"] = (
                    payload.get("device_id")
                )

                scope["platform"] = (
                    payload.get("platform")
                )

            except Exception as e:

                print(
                    "JWT ERROR:",
                    str(e)
                )

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