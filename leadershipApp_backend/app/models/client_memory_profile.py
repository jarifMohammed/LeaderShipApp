import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, UUID, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class ClientMemoryProfile(Base):
    __tablename__ = "client_memory_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    executive_summary = Column(Text, nullable=True)
    leadership_style_and_patterns = Column(JSON_TYPE, default=dict, nullable=False)
    stakeholder_map = Column(JSON_TYPE, default=dict, nullable=False)
    coach_private_notes = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

