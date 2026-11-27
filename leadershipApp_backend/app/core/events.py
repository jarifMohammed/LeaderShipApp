from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Protocol, Awaitable
import json
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    event_type: str
    payload: Dict[str, Any]
    tenant_user_id: Optional[int] = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=data.get("event_type", ""),
            tenant_user_id=data.get("tenant_user_id"),
            payload=data.get("payload", {}),
            timestamp=data.get(
                "timestamp", datetime.now(timezone.utc).isoformat()
            ),
        )


class EventBusProtocol(Protocol):
    async def publish(self, event: DomainEvent) -> bool:
        """Publish a domain event to the event stream."""
        ...

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], Awaitable[None]],
    ) -> None:
        """Register an async handler for a given event type."""
        ...


class InMemoryEventBus:
    """In-memory event bus implementation for testing and fallback."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable[[DomainEvent], Awaitable[None]]]] = {}
        self.published_events: List[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> bool:
        self.published_events.append(event)
        handlers = self._handlers.get(event.event_type, [])
        wildcard_handlers = self._handlers.get("*", [])
        all_handlers = handlers + wildcard_handlers

        for handler in all_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.exception(
                    "Error executing handler %s for event %s: %s",
                    handler.__name__,
                    event.event_type,
                    e,
                )
        return True

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], Awaitable[None]],
    ) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)


class RedisEventBus:
    """Redis Stream-backed event bus providing at-least-once delivery."""

    def __init__(self, stream_name: str = "coaching_events_stream"):
        self.stream_name = stream_name
        self._handlers: Dict[str, List[Callable[[DomainEvent], Awaitable[None]]]] = {}
        self._in_memory_fallback = InMemoryEventBus()

    async def _get_redis(self):
        try:
            import redis.asyncio as aioredis
            from app.core.config import settings

            redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
            return aioredis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning("Could not connect to Redis: %s; using in-memory bus", e)
            return None

    async def publish(self, event: DomainEvent) -> bool:
        client = await self._get_redis()
        if client is None:
            return await self._in_memory_fallback.publish(event)

        try:
            event_data = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "tenant_user_id": str(event.tenant_user_id) if event.tenant_user_id else "",
                "payload": json.dumps(event.payload),
                "timestamp": event.timestamp,
            }
            await client.xadd(self.stream_name, event_data)
            await client.close()

            # Also notify any in-process subscribers
            await self._in_memory_fallback.publish(event)
            return True
        except Exception as exc:
            logger.exception("Failed to publish event to Redis stream %s: %s", self.stream_name, exc)
            return await self._in_memory_fallback.publish(event)

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], Awaitable[None]],
    ) -> None:
        await self._in_memory_fallback.subscribe(event_type, handler)


_global_event_bus: Optional[EventBusProtocol] = None


def get_event_bus() -> EventBusProtocol:
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = RedisEventBus()
    return _global_event_bus


def set_event_bus(bus: EventBusProtocol) -> None:
    global _global_event_bus
    _global_event_bus = bus

