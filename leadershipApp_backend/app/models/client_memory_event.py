import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UUID, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class ClientMemoryEvent(Base):
    __tablename__ = "client_memory_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type = Column(String(50), nullable=False)  # ai_chat, coach_session, admin_manual
    source_id = Column(String(255), nullable=True)
    diff_summary = Column(Text, nullable=False)
    payload_diff = Column(JSON_TYPE, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

