"""Add Lemon Squeezy subscription fields to users table.

Revision ID: 20260831_0005
Revises: 20260821_0004
Create Date: 2026-08-31
"""

from alembic import op
import sqlalchemy as sa

revision = "20260831_0005"
down_revision = "20260821_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add subscription columns to users table
    op.add_column(
        "users",
        sa.Column(
            "subscription_tier",
            sa.String(20),
            nullable=False,
            server_default="free",
        ),
    )
    op.add_column(
        "users",
        sa.Column("ls_customer_id", sa.String(255), nullable=True, unique=True),
    )
    op.add_column(
        "users",
        sa.Column("ls_subscription_id", sa.String(255), nullable=True, unique=True),
    )
    op.add_column(
        "users",
        sa.Column("subscription_status", sa.String(30), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "subscription_current_period_end",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Ensure existing rows have the default value (server_default handles new
    # rows, but existing rows need an explicit UPDATE on some databases)
    op.execute("UPDATE users SET subscription_tier = 'free' WHERE subscription_tier IS NULL")


def downgrade() -> None:
    op.drop_column("users", "subscription_current_period_end")
    op.drop_column("users", "subscription_status")
    op.drop_column("users", "ls_subscription_id")
    op.drop_column("users", "ls_customer_id")
    op.drop_column("users", "subscription_tier")
