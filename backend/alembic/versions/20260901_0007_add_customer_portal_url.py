"""Add customer_portal_url to users table.

Revision ID: 20260901_0007
Revises: 20260831_0006
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa

revision = "20260901_0007"
down_revision = "20260831_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("customer_portal_url", sa.String(2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "customer_portal_url")
