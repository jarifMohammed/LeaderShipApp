import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.events import InMemoryEventBus
from app.core.outbox import notify_outbox_daemon
from app.workers.outbox_daemon import OutboxDaemon


class TestOutboxDaemon(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bus = InMemoryEventBus()
        self.daemon = OutboxDaemon(
            batch_size=10,
            min_poll_interval=0.1,
            max_poll_interval=0.5,
            backoff_factor=2.0,
            event_bus=self.bus,
        )

    async def test_initial_status(self):
        """Verify daemon initial configuration and diagnostic state."""
        status = self.daemon.get_status()
        self.assertFalse(status["running"])
        self.assertEqual(status["batch_size"], 10)
        self.assertEqual(status["total_published"], 0)
        self.assertEqual(status["total_polls"], 0)
        self.assertEqual(status["current_poll_interval"], 0.1)

    async def test_daemon_runs_and_stops_gracefully(self):
        """Verify daemon can start, execute poll cycles, and stop cleanly upon request."""
        with patch("app.workers.outbox_daemon.OutboxRelay.publish_pending", new_callable=AsyncMock) as mock_publish:
            mock_publish.return_value = 0

            # Run daemon task in background
            daemon_task = asyncio.create_task(self.daemon.run())
            await asyncio.sleep(0.15)

            status = self.daemon.get_status()
            self.assertTrue(status["running"])
            self.assertGreater(status["total_polls"], 0)

            # Signal stop
            await self.daemon.stop()
            await asyncio.wait_for(daemon_task, timeout=1.0)

            self.assertFalse(self.daemon.get_status()["running"])
            self.assertTrue(daemon_task.done())

    async def test_daemon_resets_interval_on_active_batches(self):
        """Verify daemon resets poll interval to min_poll_interval when events are published."""
        self.daemon.current_poll_interval = 0.4  # Simulated backed-off state

        with patch("app.workers.outbox_daemon.OutboxRelay.publish_pending", new_callable=AsyncMock) as mock_publish:
            mock_publish.return_value = 5  # 5 events published

            daemon_task = asyncio.create_task(self.daemon.run())
            await asyncio.sleep(0.05)
            await self.daemon.stop()
            await daemon_task

            # Interval should reset to min_poll_interval (0.1s)
            self.assertEqual(self.daemon.current_poll_interval, 0.1)
            self.assertGreaterEqual(self.daemon.total_published, 5)

    async def test_daemon_wakes_up_immediately_on_signal(self):
        """Verify daemon wakes up immediately when notify_outbox_daemon() is called."""
        self.daemon.min_poll_interval = 10.0  # High timeout so only wake signal can wake it
        self.daemon.max_poll_interval = 10.0
        self.daemon.current_poll_interval = 10.0

        with patch("app.workers.outbox_daemon.OutboxRelay.publish_pending", new_callable=AsyncMock) as mock_publish:
            mock_publish.return_value = 0

            daemon_task = asyncio.create_task(self.daemon.run())
            await asyncio.sleep(0.05)
            initial_polls = self.daemon.total_polls

            # Trigger wake signal
            notify_outbox_daemon()
            await asyncio.sleep(0.08)

            # Should have polled again without waiting 10s
            self.assertGreater(self.daemon.total_polls, initial_polls)

            await self.daemon.stop()
            await daemon_task


if __name__ == "__main__":
    unittest.main()

