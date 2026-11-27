"""add executive coaching and outbox tables

Revision ID: f4c2e8a1d75b
Revises: b1c9e48a7f13
Create Date: 2026-11-03 13:45:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f4c2e8a1d75b"
down_revision = "b1c9e48a7f13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. client_memory_profiles
    op.create_table(
        "client_memory_profiles",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("executive_summary", sa.Text(), nullable=True),
        sa.Column("leadership_style_and_patterns", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("stakeholder_map", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("coach_private_notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_client_memory_profiles_user_id", "client_memory_profiles", ["user_id"])

    # 2. client_goals
    op.create_table(
        "client_goals",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="exploring"),
        sa.Column("readiness_stage", sa.String(length=50), nullable=True, server_default="unready"),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="ai_chat"),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("evidence_log", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_client_goals_user_id", "client_goals", ["user_id"])
    op.create_index("ix_client_goals_status", "client_goals", ["status"])

    # 3. coach_sessions
    op.create_table(
        "coach_sessions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "uploaded_by_admin_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("session_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("file_path_or_url", sa.String(length=1024), nullable=True),
        sa.Column("raw_transcript", sa.Text(), nullable=True),
        sa.Column("extracted_summary", sa.Text(), nullable=True),
        sa.Column("extracted_facts", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("processing_status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_coach_sessions_user_id", "coach_sessions", ["user_id"])
    op.create_index("ix_coach_sessions_uploaded_by_admin_id", "coach_sessions", ["uploaded_by_admin_id"])
    op.create_index("ix_coach_sessions_processing_status", "coach_sessions", ["processing_status"])

    # 4. client_memory_events
    op.create_table(
        "client_memory_events",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("diff_summary", sa.Text(), nullable=False),
        sa.Column("payload_diff", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_client_memory_events_user_id", "client_memory_events", ["user_id"])
    op.create_index("ix_client_memory_events_created_at", "client_memory_events", ["created_at"])

    # 5. outbox_events
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("tenant_user_id", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_outbox_events_event_type", "outbox_events", ["event_type"])
    op.create_index("ix_outbox_events_tenant_user_id", "outbox_events", ["tenant_user_id"])
    op.create_index("ix_outbox_events_status", "outbox_events", ["status"])
    op.create_index("ix_outbox_events_created_at", "outbox_events", ["created_at"])

    # 6. Alter messages table: add turn_diagnostics
    op.add_column(
        "messages",
        sa.Column("turn_diagnostics", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    # 6. Drop column from messages
    op.drop_column("messages", "turn_diagnostics")

    # 5. outbox_events
    op.drop_index("ix_outbox_events_created_at", table_name="outbox_events")
    op.drop_index("ix_outbox_events_status", table_name="outbox_events")
    op.drop_index("ix_outbox_events_tenant_user_id", table_name="outbox_events")
    op.drop_index("ix_outbox_events_event_type", table_name="outbox_events")
    op.drop_table("outbox_events")

    # 4. client_memory_events
    op.drop_index("ix_client_memory_events_created_at", table_name="client_memory_events")
    op.drop_index("ix_client_memory_events_user_id", table_name="client_memory_events")
    op.drop_table("client_memory_events")

    # 3. coach_sessions
    op.drop_index("ix_coach_sessions_processing_status", table_name="coach_sessions")
    op.drop_index("ix_coach_sessions_uploaded_by_admin_id", table_name="coach_sessions")
    op.drop_index("ix_coach_sessions_user_id", table_name="coach_sessions")
    op.drop_table("coach_sessions")

    # 2. client_goals
    op.drop_index("ix_client_goals_status", table_name="client_goals")
    op.drop_index("ix_client_goals_user_id", table_name="client_goals")
    op.drop_table("client_goals")

    # 1. client_memory_profiles
    op.drop_index("ix_client_memory_profiles_user_id", table_name="client_memory_profiles")
    op.drop_table("client_memory_profiles")

