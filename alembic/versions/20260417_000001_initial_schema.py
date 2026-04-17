"""Initial schema baseline

Revision ID: 20260417_000001
Revises: None
Create Date: 2026-04-17 10:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260417_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "department",
        sa.Column("dept_id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("dept_name", sa.String(), nullable=False),
    )
    op.create_index("ix_department_dept_name", "department", ["dept_name"], unique=True)

    op.create_table(
        "role",
        sa.Column("role_id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("role_name", sa.String(), nullable=False),
    )
    op.create_index("ix_role_role_name", "role", ["role_name"], unique=False)

    op.create_table(
        "role_department",
        sa.Column("r_d_id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("dept_id", sa.Integer(), nullable=False),
    )
    op.create_index("ix_role_department_role_id", "role_department", ["role_id"], unique=False)
    op.create_index("ix_role_department_dept_id", "role_department", ["dept_id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("dept_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("create_time", sa.String(), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_password", "users", ["password"], unique=False)
    op.create_index("ix_users_dept_id", "users", ["dept_id"], unique=False)
    op.create_index("ix_users_role_id", "users", ["role_id"], unique=False)

    op.create_table(
        "user_profile",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True, nullable=False),
        sa.Column("answer_style", sa.String(), nullable=False),
        sa.Column("preferred_language", sa.String(), nullable=False),
        sa.Column("preferred_topics", sa.String(), nullable=False),
        sa.Column("prefers_citations", sa.Boolean(), nullable=False),
        sa.Column("allow_web_search", sa.Boolean(), nullable=False),
        sa.Column("profile_notes", sa.String(), nullable=False),
        sa.Column("created_time", sa.String(), nullable=False),
        sa.Column("updated_time", sa.String(), nullable=False),
    )
    op.create_index("ix_user_profile_answer_style", "user_profile", ["answer_style"], unique=False)
    op.create_index("ix_user_profile_preferred_language", "user_profile", ["preferred_language"], unique=False)

    op.create_table(
        "file",
        sa.Column("file_id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("dept_id", sa.Integer(), nullable=False),
        sa.Column("create_time", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
    )
    op.create_index("ix_file_user_id", "file", ["user_id"], unique=False)
    op.create_index("ix_file_dept_id", "file", ["dept_id"], unique=False)
    op.create_index("ix_file_file_name", "file", ["file_name"], unique=False)
    op.create_index("ix_file_file_path", "file", ["file_path"], unique=False)
    op.create_index("ix_file_file_type", "file", ["file_type"], unique=False)
    op.create_index("ix_file_state", "file", ["state"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_file_state", table_name="file")
    op.drop_index("ix_file_file_type", table_name="file")
    op.drop_index("ix_file_file_path", table_name="file")
    op.drop_index("ix_file_file_name", table_name="file")
    op.drop_index("ix_file_dept_id", table_name="file")
    op.drop_index("ix_file_user_id", table_name="file")
    op.drop_table("file")

    op.drop_index("ix_user_profile_preferred_language", table_name="user_profile")
    op.drop_index("ix_user_profile_answer_style", table_name="user_profile")
    op.drop_table("user_profile")

    op.drop_index("ix_users_role_id", table_name="users")
    op.drop_index("ix_users_dept_id", table_name="users")
    op.drop_index("ix_users_password", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_role_department_dept_id", table_name="role_department")
    op.drop_index("ix_role_department_role_id", table_name="role_department")
    op.drop_table("role_department")

    op.drop_index("ix_role_role_name", table_name="role")
    op.drop_table("role")

    op.drop_index("ix_department_dept_name", table_name="department")
    op.drop_table("department")
