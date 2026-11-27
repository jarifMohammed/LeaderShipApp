"""add processed events table for consumer idempotency

Revision ID: a7e3d1b94c20
Revises: f4c2e8a1d75b
Create Date: 2026-11-04 01:25:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a7e3d1b94c20"
down_revision = "f4c2e8a1d75b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processed_events",
        sa.Column("id", sa.String(length=255), primary_key=True),
        sa.Column("event_id", sa.String(length=100), nullable=False),
        sa.Column("handler_name", sa.String(length=100), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_processed_events_event_id", "processed_events", ["event_id"])
    op.create_index("ix_processed_events_handler_name", "processed_events", ["handler_name"])


def downgrade() -> None:
    op.drop_index("ix_processed_events_handler_name", table_name="processed_events")
    op.drop_index("ix_processed_events_event_id", table_name="processed_events")
    op.drop_table("processed_events")

