import redis

from app.config import settings


def redis_available(timeout: float = 2.0) -> bool:
    try:
        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=timeout)
        client.ping()
        return True
    except Exception:
        return False
