"""Add composite index on meal_plans for usage limit counting.

Revision ID: 20260831_0006
Revises: 20260831_0005
Create Date: 2026-08-31
"""

from alembic import op

revision = "20260831_0006"
down_revision = "20260831_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_meal_plans_user_created",
        "meal_plans",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_meal_plans_user_created", table_name="meal_plans")
