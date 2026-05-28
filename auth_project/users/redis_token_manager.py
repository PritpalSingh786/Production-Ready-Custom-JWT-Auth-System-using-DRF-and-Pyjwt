import redis
from datetime import datetime

from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

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
        # Single hash key for this user
        user_tokens_key = f"hash-rt-for-user-{user_id}"
        
        # Token data as JSON string
        token_data = {
            "jti": jti,
            "user_id": str(user_id),
            "device_id": str(device_id) if device_id else None,
            "platform": platform,
            "device_name": device_name,
            "ip_address": ip_address,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store in hash with jti as field
        self.redis.hset(user_tokens_key, jti, json.dumps(token_data))
        
        # Set expiry for the entire hash (all tokens of this user)
        ttl_seconds = settings.REFRESH_TOKEN_LIFETIME * 24 * 60 * 60
        self.redis.expire(user_tokens_key, ttl_seconds)
        
        # Optional: Maintain device to token mapping
        # if device_id:
        #     device_token_key = f"device:{device_id}:token"
        #     self.redis.setex(device_token_key, ttl_seconds, jti)
        
        return True

redis_token_manager = RedisTokenManager()