from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func
from app.db.base import Base


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    # Composite unique key: f"{event_id}:{handler_name}"
    id = Column(String(255), primary_key=True)
    event_id = Column(String(100), nullable=False, index=True)
    handler_name = Column(String(100), nullable=False, index=True)
    processed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

