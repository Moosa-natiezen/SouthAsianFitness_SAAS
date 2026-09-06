"""Add pgvector extension and user_memories table

Revision ID: 20260906_0011
Revises: 20260901_0010
Create Date: 2026-09-06 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "20260906_0011"
down_revision: str | Sequence[str] | None = "20260901_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create user_memories table
    op.create_table(
        "user_memories",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_memories")),
    )

    # Create index on user_id for efficient filtering
    op.create_index(
        op.f("ix_user_memories_user_id"),
        "user_memories",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop table and indexes
    op.drop_index(op.f("ix_user_memories_user_id"), table_name="user_memories")
    op.drop_table("user_memories")

    # Note: We don't drop the vector extension as it might be used by other tables
    # op.execute("DROP EXTENSION IF EXISTS vector")
