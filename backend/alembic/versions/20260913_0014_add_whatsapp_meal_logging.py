"""add whatsapp meal logging tables

Revision ID: 20260913_0014
Revises: 20260911_0013
Create Date: 2026-09-13

Adds:
- users.whatsapp_phone (E.164 digits, indexed — the canonical phone linkage
  on the user row; uniqueness is enforced on whatsapp_links)
- whatsapp_links (audit/binding table mirroring the phone→user mapping)
- food_log_entries (meals logged via WhatsApp chat with LLM-estimated macros)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260913_0014"
down_revision: str | Sequence[str] | None = "20260911_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("whatsapp_phone", sa.String(length=20), nullable=True),
    )
    op.create_index(
        op.f("ix_users_whatsapp_phone"),
        "users",
        ["whatsapp_phone"],
        unique=False,
    )

    op.create_table(
        "whatsapp_links",
        sa.Column("phone_e164", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_e164", name="uq_whatsapp_links_phone"),
        sa.UniqueConstraint("user_id", name="uq_whatsapp_links_user"),
    )
    op.create_index(
        op.f("ix_whatsapp_links_phone_e164"), "whatsapp_links", ["phone_e164"], unique=False
    )
    op.create_index(
        op.f("ix_whatsapp_links_user_id"), "whatsapp_links", ["user_id"], unique=False
    )

    op.create_table(
        "food_log_entries",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("logged_on", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("raw_text", sa.String(length=1000), nullable=False),
        sa.Column("food_items_json", sa.String(length=2000), nullable=False),
        sa.Column("calories", sa.Numeric(8, 2), nullable=False),
        sa.Column("protein_g", sa.Numeric(7, 2), nullable=False),
        sa.Column("carbs_g", sa.Numeric(7, 2), nullable=False),
        sa.Column("fat_g", sa.Numeric(7, 2), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "calories >= 0 AND protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0",
            name="positive_food_log_macros",
        ),
    )
    op.create_index(
        op.f("ix_food_log_entries_user_id"), "food_log_entries", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_food_log_entries_logged_on"), "food_log_entries", ["logged_on"], unique=False
    )
    op.create_index(
        "ix_food_log_entries_user_date",
        "food_log_entries",
        ["user_id", "logged_on"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_food_log_entries_user_date", table_name="food_log_entries")
    op.drop_index(op.f("ix_food_log_entries_logged_on"), table_name="food_log_entries")
    op.drop_index(op.f("ix_food_log_entries_user_id"), table_name="food_log_entries")
    op.drop_table("food_log_entries")

    op.drop_index(op.f("ix_whatsapp_links_user_id"), table_name="whatsapp_links")
    op.drop_index(op.f("ix_whatsapp_links_phone_e164"), table_name="whatsapp_links")
    op.drop_table("whatsapp_links")

    op.drop_index(op.f("ix_users_whatsapp_phone"), table_name="users")
    op.drop_column("users", "whatsapp_phone")
