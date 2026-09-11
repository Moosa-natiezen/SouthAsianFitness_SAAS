"""Add UTM attribution columns to users.

Revision ID: 20260911_0012
Revises: be7198ae526d
Create Date: 2026-09-11
"""

import sqlalchemy as sa
from alembic import op

revision = "20260911_0012"
down_revision = "be7198ae526d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("utm_source", sa.String(200), nullable=True))
    op.add_column("users", sa.Column("utm_medium", sa.String(200), nullable=True))
    op.add_column("users", sa.Column("utm_campaign", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "utm_campaign")
    op.drop_column("users", "utm_medium")
    op.drop_column("users", "utm_source")
