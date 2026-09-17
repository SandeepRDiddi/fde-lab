"""One-time-use storage for OIDC `state`/`nonce` values.

Backed by Redis (the same instance the rest of the platform uses for
time-boxed session state, per architecture.md's data layer) so the launch
service can run more than one replica. Falls back to an in-process dict when
REDIS_URL isn't set, which is enough for local dev and unit tests.
"""
import time
from typing import Optional

from .config import settings

try:
    import redis as redis_lib
except ImportError:  # pragma: no cover - redis is an optional local-dev dep
    redis_lib = None


class _InMemoryStore:
    def __init__(self) -> None:
        self._data: dict = {}

    def setex(self, key: str, ttl: int, value: str) -> None:
        self._data[key] = (value, time.monotonic() + ttl)

    def get(self, key: str) -> Optional[str]:
        entry = self._data.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            self._data.pop(key, None)
            return None
        return value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)


class OneTimeStateStore:
    """Stores a value for `ttl` seconds; `pop` returns it exactly once."""

    def __init__(self) -> None:
        if settings.redis_url and redis_lib is not None:
            self._backend = redis_lib.from_url(settings.redis_url, decode_responses=True)
        else:
            self._backend = _InMemoryStore()

    def put(self, key: str, value: str, ttl: int) -> None:
        self._backend.setex(key, ttl, value)

    def pop(self, key: str) -> Optional[str]:
        value = self._backend.get(key)
        if value is not None:
            self._backend.delete(key)
        return value

    def peek(self, key: str) -> Optional[str]:
        return self._backend.get(key)


state_store = OneTimeStateStore()
