"""Add TDEE target columns to user_profiles.

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa

revision = "20260901_0009"
down_revision = "20260901_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column("target_calories", sa.Integer(), nullable=True),
    )
    op.add_column(
        "user_profiles",
        sa.Column("target_protein_g", sa.Numeric(6, 1), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "target_protein_g")
    op.drop_column("user_profiles", "target_calories")
