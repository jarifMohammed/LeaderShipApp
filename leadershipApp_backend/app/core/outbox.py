import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import DomainEvent, EventBusProtocol, get_event_bus
from app.models.outbox_event import OutboxEvent

logger = logging.getLogger(__name__)

_daemon_wake_event: Optional[asyncio.Event] = None


def get_outbox_wake_event() -> asyncio.Event:
    global _daemon_wake_event
    if _daemon_wake_event is None:
        _daemon_wake_event = asyncio.Event()
    return _daemon_wake_event


def notify_outbox_daemon() -> None:
    """Signals any running outbox worker daemon to immediately poll pending events."""
    global _daemon_wake_event
    if _daemon_wake_event is not None:
        _daemon_wake_event.set()


class OutboxRelay:
    @staticmethod
    async def enqueue(
        db: AsyncSession,
        event_type: str,
        payload: Dict[str, Any],
        tenant_user_id: Optional[int] = None,
    ) -> OutboxEvent:
        """
        Atomically records an event inside the caller's active database transaction.
        The event is stored as 'pending' and published only after transaction commit.
        """
        event = OutboxEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            tenant_user_id=tenant_user_id,
            payload=payload,
            status="pending",
            retry_count=0,
        )
        db.add(event)
        notify_outbox_daemon()
        return event

    @staticmethod
    async def publish_pending(
        db: AsyncSession,
        event_bus: Optional[EventBusProtocol] = None,
        limit: int = 50,
    ) -> int:
        """
        Fetches up to `limit` pending outbox events using SKIP LOCKED concurrency control
        and publishes them to the event bus.
        Marks successfully published events as 'published'.
        """
        bus = event_bus or get_event_bus()

        # Concurrency-safe row-level lock: skips already locked rows across competing worker processes
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == "pending")
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await db.execute(stmt)
        events: List[OutboxEvent] = result.scalars().all()

        published_count = 0
        for ev in events:
            domain_event = DomainEvent(
                event_id=str(ev.id),
                event_type=ev.event_type,
                tenant_user_id=ev.tenant_user_id,
                payload=ev.payload,
                timestamp=ev.created_at.isoformat() if ev.created_at else datetime.now(timezone.utc).isoformat(),
            )
            try:
                success = await bus.publish(domain_event)
                if success:
                    ev.status = "published"
                    ev.published_at = datetime.now(timezone.utc)
                    published_count += 1
                else:
                    ev.retry_count += 1
                    if ev.retry_count >= 5:
                        ev.status = "failed"
            except Exception as e:
                logger.exception("Failed to publish outbox event %s (%s): %s", ev.id, ev.event_type, e)
                ev.retry_count += 1
                if ev.retry_count >= 5:
                    ev.status = "failed"

        if events:
            await db.commit()

        return published_count

