import redis
from datetime import datetime

from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class RedisTokenManager:

    def __init__(self):
        self.redis = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_keepalive=True,
            retry_on_timeout=True,
            health_check_interval=30
        )

    def store_refresh_token(
        self,
        user_id,
        jti,
        device_id,
        platform="web",
        device_name="",
        ip_address=""
    ):
        key = f"rt:{jti}"

        token_data = {
            "user_id": str(user_id),
            "device_id": str(device_id) if device_id else None,
            "platform": platform,
            "device_name": device_name,
            "ip_address": ip_address,
            "created_at": datetime.utcnow().isoformat()
        }

        self.redis.hset(key, mapping=token_data)

        ttl_seconds = settings.REFRESH_TOKEN_LIFETIME * 24 * 60 * 60

        self.redis.expire(key, ttl_seconds)

        user_tokens_key = f"user:{user_id}:tokens"

        self.redis.sadd(user_tokens_key, jti)
        self.redis.expire(user_tokens_key, ttl_seconds)

        if device_id:
            self.redis.setex(
                f"device:{device_id}:token",
                ttl_seconds,
                jti
            )

    def get_refresh_token(self, jti):
        key = f"rt:{jti}"

        data = self.redis.hgetall(key)

        return data if data else None

    def delete_refresh_token(self, jti):
        token_data = self.get_refresh_token(jti)

        if token_data:
            user_id = token_data["user_id"]
            device_id = token_data.get("device_id")

            self.redis.srem(f"user:{user_id}:tokens", jti)

            if device_id:
                self.redis.delete(f"device:{device_id}:token")

            return bool(self.redis.delete(f"rt:{jti}"))

        return False

    def blacklist_token(self, jti, reason="revoked"):
        ttl = self.redis.ttl(f"rt:{jti}")

        if ttl <= 0:
            ttl = 86400

        self.redis.setex(f"bl:{jti}", ttl, reason)

        return True

    def is_blacklisted(self, jti):
        return self.redis.exists(f"bl:{jti}") > 0

    def blacklist_token_by_value(self, token_str, reason="revoked"):
        try:
            import jwt

            payload = jwt.decode(
                token_str,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_signature": False}
            )

            jti = payload.get("jti")

            if jti:
                return self.blacklist_token(jti, reason)

        except Exception:
            pass

        return False

    def get_user_active_tokens(self, user_id):
        user_tokens_key = f"user:{user_id}:tokens"

        jtis = self.redis.smembers(user_tokens_key)

        active_tokens = []

        for jti in jtis:
            token_data = self.get_refresh_token(jti)

            if token_data and not self.is_blacklisted(jti):
                token_data["jti"] = jti
                active_tokens.append(token_data)

        return active_tokens

    def send_session_killed_notification(self, user_id, device_id, message="Your session has been terminated"):
        """Send WebSocket notification that a session has been killed"""
        try:
            channel_layer = get_channel_layer()
            group_name = f"user_{user_id}_{device_id}"
            
            # Send to the specific device's group
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "session_killed",
                    "message": message
                }
            )
            return True
        except Exception as e:
            print(f"Error sending session killed notification: {e}")
            return False

    def revoke_all_user_tokens(self, user_id, reason="revoked_all"):
        """Revoke all tokens for a user and notify all devices"""
        user_tokens_key = f"user:{user_id}:tokens"

        jtis = self.redis.smembers(user_tokens_key)

        if not jtis:
            return 0

        # Get all device IDs before revoking
        device_ids = []
        for jti in jtis:
            token_data = self.get_refresh_token(jti)
            if token_data and token_data.get("device_id"):
                device_ids.append(token_data["device_id"])

        pipe = self.redis.pipeline()

        for jti in jtis:
            ttl = self.redis.ttl(f"rt:{jti}")

            if ttl > 0:
                pipe.setex(f"bl:{jti}", ttl, reason)

            pipe.delete(f"rt:{jti}")

            token_data = self.get_refresh_token(jti)

            if token_data and token_data.get("device_id"):
                pipe.delete(f"device:{token_data['device_id']}:token")

        pipe.delete(user_tokens_key)

        pipe.execute()

        # Send notifications to all devices
        for device_id in device_ids:
            self.send_session_killed_notification(
                user_id, 
                device_id, 
                f"Session terminated: {reason}"
            )

        return len(jtis)

    def revoke_device_tokens(self, user_id, device_id, reason="device_removed"):
        """Revoke tokens for a specific device and notify it"""
        device_token_key = f"device:{device_id}:token"

        jti = self.redis.get(device_token_key)

        if not jti:
            return 0

        token_data = self.get_refresh_token(jti)

        if token_data and token_data.get("user_id") == str(user_id):
            self.blacklist_token(jti, reason)
            self.delete_refresh_token(jti)

            # Send notification to this specific device
            self.send_session_killed_notification(
                user_id, 
                device_id, 
                f"Device session terminated: {reason}"
            )

            return 1

        return 0

    def limit_user_sessions(self, user_id, max_sessions=5):
        """Limit user sessions and notify oldest sessions being removed"""
        active_tokens = self.get_user_active_tokens(user_id)

        if len(active_tokens) <= max_sessions:
            return 0

        active_tokens.sort(key=lambda x: x.get("created_at", ""))

        tokens_to_revoke = active_tokens[:-max_sessions]

        revoked_count = 0

        for token in tokens_to_revoke:
            jti = token.get("jti")
            device_id = token.get("device_id")

            if jti:
                self.blacklist_token(jti, "session_limit_exceeded")
                self.delete_refresh_token(jti)

                # Notify the device being revoked
                if device_id:
                    self.send_session_killed_notification(
                        user_id,
                        device_id,
                        "Session limit exceeded. Oldest session terminated."
                    )

                revoked_count += 1

        return revoked_count


redis_token_manager = RedisTokenManager()