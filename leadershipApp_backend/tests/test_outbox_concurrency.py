import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import uuid

from sqlalchemy.sql import Select
from app.core.events import DomainEvent, InMemoryEventBus
from app.core.outbox import OutboxRelay, get_outbox_wake_event, notify_outbox_daemon
from app.models.outbox_event import OutboxEvent


class TestOutboxConcurrencyAndRelay(unittest.IsolatedAsyncioTestCase):
    async def test_enqueue_creates_pending_event_and_notifies_daemon(self):
        """Verify enqueue records an event as pending and signals the daemon wake event."""
        mock_db = MagicMock()
        wake_event = get_outbox_wake_event()
        wake_event.clear()

        event = await OutboxRelay.enqueue(
            db=mock_db,
            event_type="chat.turn.completed",
            tenant_user_id=101,
            payload={"turn": 1, "message": "growth goal"},
        )

        self.assertEqual(event.event_type, "chat.turn.completed")
        self.assertEqual(event.tenant_user_id, 101)
        self.assertEqual(event.status, "pending")
        self.assertEqual(event.retry_count, 0)
        self.assertTrue(mock_db.add.called)
        self.assertTrue(wake_event.is_set(), "Daemon wake event should be set after enqueue")

    async def test_publish_pending_applies_skip_locked(self):
        """Verify publish_pending constructs a query using with_for_update(skip_locked=True)."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        bus = InMemoryEventBus()
        published = await OutboxRelay.publish_pending(db=mock_db, event_bus=bus, limit=25)

        self.assertEqual(published, 0)
        self.assertTrue(mock_db.execute.called)

        # Inspect statement passed to db.execute
        stmt = mock_db.execute.call_args[0][0]
        self.assertIsInstance(stmt, Select)
        # Verify FOR UPDATE SKIP LOCKED clause is attached to AST
        self.assertTrue(
            hasattr(stmt, "_for_update_arg") and stmt._for_update_arg is not None,
            "Statement must have for_update_arg configured",
        )
        self.assertTrue(stmt._for_update_arg.skip_locked, "SKIP LOCKED must be set to True")

    async def test_publish_pending_publishes_and_updates_status(self):
        """Verify pending events are published to the event bus and marked 'published'."""
        mock_db = AsyncMock()
        ev1 = OutboxEvent(
            id=uuid.uuid4(),
            event_type="chat.turn.completed",
            tenant_user_id=5,
            payload={"data": "test"},
            status="pending",
            retry_count=0,
            created_at=datetime.now(timezone.utc),
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [ev1]
        mock_db.execute.return_value = mock_result

        bus = InMemoryEventBus()
        published_count = await OutboxRelay.publish_pending(db=mock_db, event_bus=bus, limit=10)

        self.assertEqual(published_count, 1)
        self.assertEqual(ev1.status, "published")
        self.assertIsNotNone(ev1.published_at)
        self.assertEqual(len(bus.published_events), 1)
        self.assertEqual(bus.published_events[0].event_type, "chat.turn.completed")
        self.assertTrue(mock_db.commit.called)

    async def test_publish_pending_retries_and_marks_failed(self):
        """Verify failed publishing increments retry_count and marks status as 'failed' after 5 retries."""
        mock_db = AsyncMock()
        ev_failing = OutboxEvent(
            id=uuid.uuid4(),
            event_type="coach.session.uploaded",
            tenant_user_id=8,
            payload={},
            status="pending",
            retry_count=4,  # Next failure will reach 5
            created_at=datetime.now(timezone.utc),
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [ev_failing]
        mock_db.execute.return_value = mock_result

        # EventBus mock that returns False (publishing failed)
        failing_bus = MagicMock()
        failing_bus.publish = AsyncMock(return_value=False)

        published_count = await OutboxRelay.publish_pending(db=mock_db, event_bus=failing_bus, limit=10)

        self.assertEqual(published_count, 0)
        self.assertEqual(ev_failing.retry_count, 5)
        self.assertEqual(ev_failing.status, "failed")
        self.assertTrue(mock_db.commit.called)


if __name__ == "__main__":
    unittest.main()

