import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UUID, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class CoachSession(Base):
    __tablename__ = "coach_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by_admin_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False)
    session_date = Column(DateTime(timezone=True), nullable=True)
    file_type = Column(String(50), nullable=False)  # audio, document
    file_path_or_url = Column(String(1024), nullable=True)
    raw_transcript = Column(Text, nullable=True)
    extracted_summary = Column(Text, nullable=True)
    extracted_facts = Column(JSON_TYPE, default=dict, nullable=False)
    processing_status = Column(
        String(50), default="queued", nullable=False, index=True
    )  # queued, transcribing, extracting, indexing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

