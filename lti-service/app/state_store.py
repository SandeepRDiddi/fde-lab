"""One-time-use storage for OIDC `state`/`nonce` values.

Backed by Redis (the same instance the rest of the platform uses for
time-boxed session state, per architecture.md's data layer) so the launch
service can run more than one replica. Falls back to an in-process dict when
REDIS_URL isn't set, which is enough for local dev and unit tests.
"""
import threading
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
        self._lock = threading.Lock()

    def setex(self, key: str, ttl: int, value: str) -> None:
        with self._lock:
            self._data[key] = (value, time.monotonic() + ttl)

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            return self._get_locked(key)

    def _get_locked(self, key: str) -> Optional[str]:
        entry = self._data.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            self._data.pop(key, None)
            return None
        return value

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def getdel(self, key: str) -> Optional[str]:
        with self._lock:
            value = self._get_locked(key)
            if value is not None:
                self._data.pop(key, None)
            return value


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
        # Atomic get-and-delete (Redis GETDEL / a lock around the in-memory
        # dict) -- a plain get-then-delete lets two near-simultaneous
        # launches both redeem the same one-time state/nonce.
        return self._backend.getdel(key)

    def peek(self, key: str) -> Optional[str]:
        return self._backend.get(key)


state_store = OneTimeStateStore()
