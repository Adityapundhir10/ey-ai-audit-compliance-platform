import json
from typing import Any, Dict, Optional
from app.core.config import get_settings


class RedisQueue:
    def __init__(self, name: str = "invoice_workflows"):
        self.name = name
        self.settings = get_settings()
        self._client = None

    def _connect(self):
        if self._client is not None:
            return self._client
        try:
            import redis
            self._client = redis.from_url(self.settings.redis_url, decode_responses=True)
            self._client.ping()
        except Exception:
            self._client = None
        return self._client

    def push(self, payload: Dict[str, Any]) -> str:
        client = self._connect()
        message = json.dumps(payload)
        if client:
            client.rpush(self.name, message)
        return message

    def pop(self, timeout: int = 2) -> Optional[Dict[str, Any]]:
        client = self._connect()
        if not client:
            return None
        item = client.blpop(self.name, timeout=timeout)
        if not item:
            return None
        _, payload = item
        return json.loads(payload)
