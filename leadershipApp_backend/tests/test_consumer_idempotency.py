import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.events import DomainEvent
from app.core.idempotency import (
    EventDeduplicator,
    idempotent_event,
    get_event_deduplicator,
)


class TestConsumerIdempotency(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.dedup = EventDeduplicator(ttl_seconds=3600)

    async def test_first_delivery_is_processed(self):
        """Verify first arrival of an event is accepted for processing."""
        async with self.dedup.acquire(event_id="ev-100", handler_name="handle_chat_turn") as should_process:
            self.assertTrue(should_process)

    async def test_duplicate_delivery_is_skipped(self):
        """Verify duplicate delivery of same event_id and handler is blocked."""
        async with self.dedup.acquire(event_id="ev-200", handler_name="handle_chat_turn") as should_process:
            self.assertTrue(should_process)

        # Second delivery of same event to same handler
        async with self.dedup.acquire(event_id="ev-200", handler_name="handle_chat_turn") as should_process:
            self.assertFalse(should_process, "Second delivery must be rejected as duplicate")

    async def test_different_handlers_process_same_event(self):
        """Verify multiple distinct handlers can independently process the same domain event."""
        event_id = "ev-300"
        async with self.dedup.acquire(event_id=event_id, handler_name="handler_analytics") as ok1:
            self.assertTrue(ok1)

        async with self.dedup.acquire(event_id=event_id, handler_name="handler_memory_update") as ok2:
            self.assertTrue(ok2, "Different handler must be permitted to process the event")

    async def test_idempotent_event_decorator(self):
        """Verify @idempotent_event decorator blocks duplicate invocations."""
        execution_count = 0

        class ConsumerService:
            @idempotent_event(handler_name="test_worker_handler")
            async def handle_event(self, event: DomainEvent):
                nonlocal execution_count
                execution_count += 1
                return f"processed-{event.event_id}"

        service = ConsumerService()
        event = DomainEvent(event_type="test.event", event_id="unique-ev-555", payload={"test": True})

        # First call -> executes
        res1 = await service.handle_event(event)
        self.assertEqual(res1, "processed-unique-ev-555")
        self.assertEqual(execution_count, 1)

        # Duplicate call -> skipped, returns None
        res2 = await service.handle_event(event)
        self.assertIsNone(res2)
        self.assertEqual(execution_count, 1, "Handler should not execute on duplicate delivery")

    async def test_failed_processing_allows_retry(self):
        """Verify that if an exception is raised, the event is NOT marked completed and can be retried."""
        event_id = "ev-fail-then-succeed"
        handler = "flaky_handler"

        # First attempt fails with an exception
        with self.assertRaises(RuntimeError):
            async with self.dedup.acquire(event_id=event_id, handler_name=handler) as should_process:
                self.assertTrue(should_process)
                raise RuntimeError("Simulated transient connection failure")

        # Second delivery (retry) should be allowed!
        async with self.dedup.acquire(event_id=event_id, handler_name=handler) as should_process:
            self.assertTrue(should_process, "Retry must be allowed after prior failure")


if __name__ == "__main__":
    unittest.main()

