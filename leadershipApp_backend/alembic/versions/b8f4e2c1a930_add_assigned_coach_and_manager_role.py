"""add assigned coach and manager role

Revision ID: b8f4e2c1a930
Revises: a7e3d1b94c20
Create Date: 2026-11-04 02:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b8f4e2c1a930"
down_revision = "a7e3d1b94c20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    try:
        op.drop_constraint("ck_users_role", "users", type_="check")
    except Exception:
        pass
    op.create_check_constraint(
        "ck_users_role", "users", "role IN ('admin', 'user', 'manager')"
    )

    op.add_column(
        "users",
        sa.Column("assigned_coach_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_assigned_coach_id",
        "users",
        "users",
        ["assigned_coach_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_users_assigned_coach_id",
        "users",
        ["assigned_coach_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_users_assigned_coach_id", table_name="users")
    op.drop_constraint("fk_users_assigned_coach_id", "users", type_="foreignkey")
    op.drop_column("users", "assigned_coach_id")

    try:
        op.drop_constraint("ck_users_role", "users", type_="check")
    except Exception:
        pass
    op.create_check_constraint(
        "ck_users_role", "users", "role IN ('admin', 'user')"
    )

