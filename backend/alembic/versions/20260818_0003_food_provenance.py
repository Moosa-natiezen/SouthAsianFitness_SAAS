"""Add food data provenance layer: food_sources table and provenance columns on foods

Revision ID: 20260818_0003
Revises: 20260817_0002
Create Date: 2026-08-18 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260818_0003"
down_revision: str | Sequence[str] | None = "20260817_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create food_source_license enum type
    op.execute(
        "CREATE TYPE food_source_license AS ENUM ("
        "'public_domain', 'cc0', 'cc_by', 'cc_by_sa', 'open_data', "
        "'proprietary_allow_redist', 'proprietary_no_redist', 'unknown')"
    )

    # 2. Create verification_status enum type
    op.execute(
        "CREATE TYPE verification_status AS ENUM ("
        "'unverified', 'pending_review', 'verified', 'conflict', 'retracted')"
    )

    # 3. Create food_sources table
    op.create_table(
        "food_sources",
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("reference_url", sa.Text(), nullable=True),
        sa.Column(
            "license_category",
            sa.Enum(
                "public_domain",
                "cc0",
                "cc_by",
                "cc_by_sa",
                "open_data",
                "proprietary_allow_redist",
                "proprietary_no_redist",
                "unknown",
                name="food_source_license",
            ),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column("attribution_text", sa.Text(), nullable=True),
        sa.Column(
            "can_store_raw_data", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "can_store_derived_values",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_food_sources")),
        sa.UniqueConstraint(
            "name", "version", name=op.f("uq_food_sources_name_version")
        ),
    )
    op.create_index(
        op.f("ix_food_sources_name"), "food_sources", ["name"], unique=False
    )

    # 4. Add provenance columns to foods table
    op.add_column(
        "foods",
        sa.Column(
            "food_source_id",
            sa.Uuid(),
            sa.ForeignKey("food_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "foods",
        sa.Column("source_identifier", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "foods",
        sa.Column("source_version", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "foods",
        sa.Column("source_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "foods",
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "foods",
        sa.Column(
            "verification_status",
            sa.Enum(
                "unverified",
                "pending_review",
                "verified",
                "conflict",
                "retracted",
                name="verification_status",
            ),
            nullable=False,
            server_default="unverified",
        ),
    )

    # 5. Add indexes for provenance columns on foods
    op.create_index(
        op.f("ix_foods_food_source_id"),
        "foods",
        ["food_source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_foods_verification_status"),
        "foods",
        ["verification_status"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_foods_verification_status"), table_name="foods")
    op.drop_index(op.f("ix_foods_food_source_id"), table_name="foods")

    # Drop columns from foods
    op.drop_column("foods", "verification_status")
    op.drop_column("foods", "imported_at")
    op.drop_column("foods", "source_date")
    op.drop_column("foods", "source_version")
    op.drop_column("foods", "source_identifier")
    op.drop_column("foods", "food_source_id")

    # Drop food_sources table
    op.drop_index(op.f("ix_food_sources_name"), table_name="food_sources")
    op.drop_table("food_sources")

    # Drop enum types
    sa.Enum(name="verification_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="food_source_license").drop(op.get_bind(), checkfirst=True)
