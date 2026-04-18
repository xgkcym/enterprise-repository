"""Add user_type column to users

Revision ID: 20260418_000002
Revises: 20260417_000001
Create Date: 2026-04-18 19:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260418_000002"
down_revision = "20260417_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("user_type", sa.String(), nullable=True))
    op.execute("UPDATE users SET user_type = 'admin' WHERE user_type IS NULL")
    op.alter_column("users", "user_type", nullable=False, server_default="user")
    op.create_index("ix_users_user_type", "users", ["user_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_user_type", table_name="users")
    op.drop_column("users", "user_type")
