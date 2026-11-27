import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UUID, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class ClientGoal(Base):
    __tablename__ = "client_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="exploring", nullable=False, index=True)  # exploring, committed, in_progress, completed, stalled
    readiness_stage = Column(String(50), default="unready", nullable=True)  # unready, exploring, preparing, ready, practicing
    source_type = Column(String(50), default="ai_chat", nullable=False)  # ai_chat, coach_session, admin_manual
    source_id = Column(String(255), nullable=True)
    evidence_log = Column(JSON_TYPE, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

