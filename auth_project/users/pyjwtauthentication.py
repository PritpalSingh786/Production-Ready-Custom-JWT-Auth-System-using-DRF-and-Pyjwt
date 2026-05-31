from rest_framework import (
    authentication,
    exceptions
)

from users.utils import (
    decode_token
)


class JWTUser:

    def __init__(
        self,
        user_id
    ):
        self.id = user_id
        self.user_id = user_id
        self.is_authenticated = True


class PyJWTAuthentication(
    authentication.BaseAuthentication
):

    def authenticate(
        self,
        request
    ):
        auth_header = request.headers.get(
            "Authorization"
        )

        if not auth_header:
            return None

        parts = auth_header.split()

        if (
            len(parts) != 2
            or parts[0].lower()
            != "bearer"
        ):
            raise exceptions.AuthenticationFailed(
                "Invalid authorization header"
            )

        payload = decode_token(
            parts[1],
            "access"
        )

        if not payload:
            raise exceptions.AuthenticationFailed(
                "Invalid or expired token"
            )

        request.device_id = payload.get(
            "device_id"
        )

        request.platform = payload.get(
            "platform"
        )

        user = JWTUser(
            payload["user_id"]
        )

        return (
            user,
            parts[1]
        )