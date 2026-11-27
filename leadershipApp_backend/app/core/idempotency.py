"""
Distributed Consumer Idempotency & Event Deduplication Tier.

Guarantees idempotent processing under at-least-once delivery semantics in distributed streams.
Prevents duplicate side-effects (e.g. duplicate goal creation, duplicate memory updates,
or duplicate vector indexing) across worker restarts or network redeliveries.

Two-layer deduplication:
1. Fast-path atomic distributed lock / key via Redis: `SET idemp:{handler}:{event_id} 1 NX EX 86400`
2. Durable persistence via PostgreSQL `processed_events` table.
3. In-memory LRU fallback for zero-dependency test/offline execution.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import functools
import logging
from typing import Any, Callable, Dict, Optional, Set
import uuid

from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.models.processed_event import ProcessedEvent

logger = logging.getLogger("app.core.idempotency")


class EventDeduplicator:
    def __init__(self, ttl_seconds: int = 86400):
        self.ttl_seconds = ttl_seconds
        # In-memory deduplication set for testing / fallback
        self._in_memory_processed: Set[str] = set()

    async def _get_redis(self):
        try:
            import redis.asyncio as aioredis
            from app.core.config import settings

            redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
            client = aioredis.from_url(redis_url, decode_responses=True)
            # Ping with short timeout to verify live connectivity
            await asyncio_wait_timeout(client.ping(), timeout=0.5)
            return client
        except Exception:
            return None

    @asynccontextmanager
    async def acquire(
        self,
        event_id: str,
        handler_name: str,
    ):
        """
        Context manager checking and acquiring processing rights for a specific event + handler.
        Yields True if this is the first delivery and caller should proceed.
        Yields False if the event was already processed or is currently in flight.
        """
        composite_key = f"{event_id}:{handler_name}"
        redis_key = f"idemp:{handler_name}:{event_id}"

        # 1. Fast in-memory check
        if composite_key in self._in_memory_processed:
            logger.info("Event %s already processed by %s (in-memory)", event_id, handler_name)
            yield False
            return

        redis_client = await self._get_redis()
        redis_locked = False

        if redis_client is not None:
            try:
                # Atomic SET IF NOT EXISTS
                is_new = await redis_client.set(
                    redis_key,
                    "in_progress",
                    nx=True,
                    ex=self.ttl_seconds,
                )
                if not is_new:
                    logger.info("Event %s already in-progress or processed by %s (Redis)", event_id, handler_name)
                    await redis_client.close()
                    yield False
                    return
                redis_locked = True
            except Exception as e:
                logger.warning("Redis idempotency check failed: %s; falling back to DB", e)

        # 2. Durable Database Check
        db_already_processed = False
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(ProcessedEvent).where(ProcessedEvent.id == composite_key)
                res = await session.execute(stmt)
                if res.scalar_one_or_none() is not None:
                    db_already_processed = True
        except Exception as e:
            logger.warning("DB idempotency check failed: %s", e)

        if db_already_processed:
            logger.info("Event %s already processed by %s (database)", event_id, handler_name)
            if redis_client and redis_locked:
                try:
                    await redis_client.set(redis_key, "completed", ex=self.ttl_seconds)
                    await redis_client.close()
                except Exception:
                    pass
            yield False
            return

        # 3. Proceed with processing
        success = False
        try:
            yield True
            success = True
        except Exception:
            # If processing failed, release Redis lock so retry can be attempted
            if redis_client and redis_locked:
                try:
                    await redis_client.delete(redis_key)
                except Exception:
                    pass
            raise
        finally:
            if success:
                # Mark as permanently processed
                self._in_memory_processed.add(composite_key)

                # Persist to database
                try:
                    async with AsyncSessionLocal() as session:
                        processed_record = ProcessedEvent(
                            id=composite_key,
                            event_id=event_id,
                            handler_name=handler_name,
                        )
                        session.add(processed_record)
                        await session.commit()
                except Exception as e:
                    logger.warning("Failed to record processed_event in DB: %s", e)

                # Update Redis status to completed
                if redis_client and redis_locked:
                    try:
                        await redis_client.set(redis_key, "completed", ex=self.ttl_seconds)
                    except Exception:
                        pass

            if redis_client:
                try:
                    await redis_client.close()
                except Exception:
                    pass


async def asyncio_wait_timeout(coro, timeout: float = 0.5):
    import asyncio
    return await asyncio.wait_for(coro, timeout=timeout)


_global_deduplicator: Optional[EventDeduplicator] = None


def get_event_deduplicator() -> EventDeduplicator:
    global _global_deduplicator
    if _global_deduplicator is None:
        _global_deduplicator = EventDeduplicator()
    return _global_deduplicator


def idempotent_event(handler_name: Optional[str] = None):
    """
    Decorator for domain event handlers ensuring exactly-once execution semantics.
    """
    def decorator(func: Callable):
        actual_handler_name = handler_name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract event argument
            event = kwargs.get("event")
            if not event and len(args) > 1:
                event = args[1]
            elif not event and len(args) == 1:
                event = args[0]

            event_id = getattr(event, "event_id", None) if event else None

            if not event_id:
                # If no event_id found, proceed without deduplication
                return await func(*args, **kwargs)

            dedup = get_event_deduplicator()
            async with dedup.acquire(event_id, handler_name=actual_handler_name) as should_process:
                if not should_process:
                    logger.info(
                        "Idempotency: Skipped duplicate delivery of event '%s' for handler '%s'",
                        event_id,
                        actual_handler_name,
                    )
                    return None
                return await func(*args, **kwargs)

        return wrapper
    return decorator

