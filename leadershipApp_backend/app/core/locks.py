import asyncio
import logging
import time
from typing import Dict, Optional

from app.core.config import settings

logger = logging.getLogger("app.locks")

_MEMORY_LOCKS: Dict[str, float] = {}
_MEMORY_LOCK_MUTEX = asyncio.Lock()


class ConversationLock:
    """
    Acquires an atomic distributed lock (lock:conv:{id}) with TTL (default 60s)
    to prevent double-send races or concurrent message overwrites.
    Falls back gracefully to an in-memory lock if Redis is unavailable in tests or offline.
    """

    def __init__(self, conversation_id: str, ttl: int = 60):
        self.lock_key = f"lock:conv:{conversation_id}"
        self.ttl = ttl
        self.acquired = False
        self._redis_client = None

    async def _get_redis(self):
        try:
            import redis.asyncio as aioredis
            redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
            client = aioredis.from_url(redis_url, decode_responses=True)
            # Ping to verify active connection
            await client.ping()
            return client
        except Exception:
            return None

    async def acquire(self) -> bool:
        """Attempts to acquire the lock. Returns True if acquired, False if already locked."""
        # 1. Try Redis distributed lock
        redis_client = await self._get_redis()
        if redis_client is not None:
            self._redis_client = redis_client
            try:
                res = await redis_client.set(self.lock_key, "locked", nx=True, ex=self.ttl)
                if res:
                    self.acquired = True
                    return True
                else:
                    await redis_client.close()
                    self._redis_client = None
                    return False
            except Exception as e:
                logger.warning("Redis lock acquisition failed (%s); falling back to in-memory lock", e)
                try:
                    await redis_client.close()
                except Exception:
                    pass
                self._redis_client = None

        # 2. In-memory fallback
        async with _MEMORY_LOCK_MUTEX:
            now = time.monotonic()
            # Clean expired locks
            expired = [k for k, exp in _MEMORY_LOCKS.items() if exp < now]
            for k in expired:
                _MEMORY_LOCKS.pop(k, None)

            if self.lock_key in _MEMORY_LOCKS:
                return False

            _MEMORY_LOCKS[self.lock_key] = now + self.ttl
            self.acquired = True
            return True

    async def release(self) -> None:
        """Releases the lock."""
        if not self.acquired:
            return

        if self._redis_client is not None:
            try:
                await self._redis_client.delete(self.lock_key)
                await self._redis_client.close()
            except Exception:
                pass
            finally:
                self._redis_client = None

        async with _MEMORY_LOCK_MUTEX:
            _MEMORY_LOCKS.pop(self.lock_key, None)

        self.acquired = False

