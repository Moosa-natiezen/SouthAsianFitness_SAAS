"""Add VERIFIED_WITH_NOTES and REJECTED to verification_status enum.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-21
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new enum values to verification_status
    op.execute("ALTER TYPE verification_status ADD VALUE IF NOT EXISTS 'verified_with_notes'")
    op.execute("ALTER TYPE verification_status ADD VALUE IF NOT EXISTS 'rejected'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # A full downgrade would require recreating the enum type.
    pass
