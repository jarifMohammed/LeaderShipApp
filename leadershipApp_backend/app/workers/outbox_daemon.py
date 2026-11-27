"""
Dedicated Transactional Outbox Daemon Worker.

Decouples asynchronous event publishing completely from synchronous HTTP request loops.
Provides:
1. Concurrency-safe batch polling with SKIP LOCKED via OutboxRelay.
2. Adaptive polling with exponential backoff when idle (min_interval -> max_interval).
3. Immediate event-driven wakeup upon new event insertion via asyncio.Event or Redis Pub/Sub.
4. Graceful shutdown on SIGTERM / SIGINT ensuring all in-flight batches finish cleanly.
"""

import asyncio
from datetime import datetime, timezone
import logging
import signal
import sys
from typing import Any, Dict, Optional

from app.core.events import EventBusProtocol, get_event_bus
from app.core.outbox import OutboxRelay, get_outbox_wake_event
from app.db.database import AsyncSessionLocal

logger = logging.getLogger("app.workers.outbox_daemon")


class OutboxDaemon:
    def __init__(
        self,
        batch_size: int = 50,
        min_poll_interval: float = 1.0,
        max_poll_interval: float = 5.0,
        backoff_factor: float = 1.5,
        event_bus: Optional[EventBusProtocol] = None,
    ):
        self.batch_size = batch_size
        self.min_poll_interval = min_poll_interval
        self.max_poll_interval = max_poll_interval
        self.backoff_factor = backoff_factor
        self.event_bus = event_bus

        self.current_poll_interval = min_poll_interval
        self._running = False
        self._stop_event = asyncio.Event()
        self._wake_event = get_outbox_wake_event()

        self.total_published = 0
        self.total_polls = 0
        self.started_at: Optional[datetime] = None

    async def run(self) -> None:
        """Main daemon execution loop."""
        self._running = True
        self._stop_event.clear()
        self.started_at = datetime.now(timezone.utc)
        logger.info(
            "OutboxDaemon started [batch_size=%d, min_interval=%.1fs, max_interval=%.1fs]",
            self.batch_size,
            self.min_poll_interval,
            self.max_poll_interval,
        )

        bus = self.event_bus or get_event_bus()

        while not self._stop_event.is_set():
            self.total_polls += 1
            published_count = 0

            try:
                async with AsyncSessionLocal() as session:
                    published_count = await OutboxRelay.publish_pending(
                        db=session,
                        event_bus=bus,
                        limit=self.batch_size,
                    )
            except Exception as exc:
                logger.exception("OutboxDaemon encounter error during polling: %s", exc)
                published_count = 0

            self.total_published += published_count

            if published_count > 0:
                logger.info("OutboxDaemon successfully published %d events", published_count)
                # Reset interval on active work so consecutive batches drain immediately
                self.current_poll_interval = self.min_poll_interval
                # If a full batch was fetched, loop immediately to drain any backlog
                if published_count >= self.batch_size:
                    continue
            else:
                # Exponential backoff when idle
                self.current_poll_interval = min(
                    self.current_poll_interval * self.backoff_factor,
                    self.max_poll_interval,
                )

            # Wait for either poll interval timeout or an immediate wakeup signal
            try:
                self._wake_event.clear()
                # Wait with timeout; returns immediately if woken up early
                await asyncio.wait_for(
                    self._wait_for_wake_or_stop(),
                    timeout=self.current_poll_interval,
                )
            except asyncio.TimeoutError:
                # Normal interval expiry when idle
                pass

        logger.info(
            "OutboxDaemon stopped cleanly. Total events published: %d across %d polls.",
            self.total_published,
            self.total_polls,
        )

    async def _wait_for_wake_or_stop(self) -> None:
        """Awaits either a wake notification or a stop signal."""
        while not self._stop_event.is_set():
            if self._wake_event.is_set():
                logger.debug("OutboxDaemon woken up by immediate event insertion signal")
                return
            await asyncio.sleep(0.05)

    def trigger_wakeup(self) -> None:
        """Manually trigger immediate poll cycle."""
        self._wake_event.set()

    async def stop(self) -> None:
        """Signals the daemon to gracefully stop after in-flight work completes."""
        logger.info("OutboxDaemon receiving stop signal...")
        self._running = False
        self._stop_event.set()
        self._wake_event.set()

    def get_status(self) -> Dict[str, Any]:
        """Returns diagnostic telemetry for health checks and supervision."""
        return {
            "running": self._running,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "total_published": self.total_published,
            "total_polls": self.total_polls,
            "current_poll_interval": round(self.current_poll_interval, 2),
            "batch_size": self.batch_size,
        }


def setup_signal_handlers(daemon: OutboxDaemon, loop: asyncio.AbstractEventLoop) -> None:
    """Installs POSIX signal handlers for graceful shutdown."""
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(daemon.stop()))
        except (NotImplementedError, RuntimeError):
            # Fallback for Windows or non-main thread environments
            pass


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    daemon = OutboxDaemon()
    loop = asyncio.get_running_loop()
    setup_signal_handlers(daemon, loop)

    try:
        await daemon.run()
    except (asyncio.CancelledError, KeyboardInterrupt):
        await daemon.stop()


if __name__ == "__main__":
    asyncio.run(main())

