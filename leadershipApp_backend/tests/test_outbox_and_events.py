import unittest
from unittest.mock import AsyncMock, MagicMock
from app.core.events import DomainEvent, InMemoryEventBus
from app.core.outbox import OutboxRelay


class OutboxAndEventBusTests(unittest.IsolatedAsyncioTestCase):
    async def test_event_bus_subscribe_and_publish(self):
        bus = InMemoryEventBus()
        received_events = []

        async def handler(event: DomainEvent):
            received_events.append(event)

        await bus.subscribe("chat.turn.completed", handler)

        event = DomainEvent(
            event_type="chat.turn.completed",
            tenant_user_id=42,
            payload={"user_id": 42, "turn_diagnostics": {"socratic_stage": "Goal"}},
        )

        await bus.publish(event)
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].tenant_user_id, 42)
        self.assertEqual(received_events[0].event_type, "chat.turn.completed")

    async def test_outbox_relay_enqueue(self):
        mock_db = MagicMock()
        mock_db.add = MagicMock()

        event = await OutboxRelay.enqueue(
            db=mock_db,
            event_type="chat.turn.completed",
            tenant_user_id=10,
            payload={"conversation_id": "test-uuid", "user_message": "Hello"},
        )

        self.assertEqual(event.event_type, "chat.turn.completed")
        self.assertEqual(event.tenant_user_id, 10)
        self.assertEqual(event.status, "pending")
        mock_db.add.assert_called_once_with(event)


if __name__ == "__main__":
    unittest.main()
