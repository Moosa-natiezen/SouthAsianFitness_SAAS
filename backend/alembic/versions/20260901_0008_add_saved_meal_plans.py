"""Add saved_meal_plans table for AI-generated meal plans.

Revision ID: 20260901_0008
Revises: 20260901_0007
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa

revision = "20260901_0008"
down_revision = "20260901_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_meal_plans",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("target_calories", sa.Integer(), nullable=True),
        sa.Column("protein_g", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_saved_meal_plans_user_created",
        "saved_meal_plans",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_saved_meal_plans_user_created", table_name="saved_meal_plans")
    op.drop_table("saved_meal_plans")
