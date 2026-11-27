import uuid
from sqlalchemy import Column, DateTime, Integer, String, UUID, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    tenant_user_id = Column(Integer, nullable=True, index=True)
    payload = Column(JSON_TYPE, default=dict, nullable=False)
    status = Column(
        String(50), default="pending", nullable=False, index=True
    )  # pending, published, failed
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    published_at = Column(DateTime(timezone=True), nullable=True)

