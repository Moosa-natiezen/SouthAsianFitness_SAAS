"""Add database indexes for performance.

Revision ID: 20260911_0013
Revises: 20260911_0012
Create Date: 2026-09-12

Adds B-tree indexes to the remaining hot lookup paths:

- ``user_sessions.expires_at``: session validity checks and expiry-purge
  queries filter on this column; previously unindexed.
- Second FK column of every many-to-many association table: Postgres only
  indexes the leading column of a composite primary key, so reverse lookups
  ("all foods with this tag", "all regions for these preferences") and
  CASCADE deletes previously required full scans.
"""

from alembic import op

revision = "20260911_0013"
down_revision = "20260911_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Session expiry lookups / purge jobs scan user_sessions without an index.
    op.create_index(
        op.f("ix_user_sessions_expires_at"),
        "user_sessions",
        ["expires_at"],
        unique=False,
    )

    # Association tables: index the trailing FK of each composite PK so
    # reverse lookups and ON DELETE CASCADE use an index instead of a scan.
    op.create_index(
        op.f("ix_food_regions_region_id"),
        "food_regions",
        ["region_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_food_cuisine_tags_cuisine_tag_id"),
        "food_cuisine_tags",
        ["cuisine_tag_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_food_dietary_tags_dietary_tag_id"),
        "food_dietary_tags",
        ["dietary_tag_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_profile_dietary_tags_dietary_tag_id"),
        "user_profile_dietary_tags",
        ["dietary_tag_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_preference_dietary_tags_dietary_tag_id"),
        "user_preference_dietary_tags",
        ["dietary_tag_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_preference_cuisine_tags_cuisine_tag_id"),
        "user_preference_cuisine_tags",
        ["cuisine_tag_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_preference_regions_region_id"),
        "user_preference_regions",
        ["region_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_user_preference_regions_region_id"),
        table_name="user_preference_regions",
    )
    op.drop_index(
        op.f("ix_user_preference_cuisine_tags_cuisine_tag_id"),
        table_name="user_preference_cuisine_tags",
    )
    op.drop_index(
        op.f("ix_user_preference_dietary_tags_dietary_tag_id"),
        table_name="user_preference_dietary_tags",
    )
    op.drop_index(
        op.f("ix_user_profile_dietary_tags_dietary_tag_id"),
        table_name="user_profile_dietary_tags",
    )
    op.drop_index(
        op.f("ix_food_dietary_tags_dietary_tag_id"),
        table_name="food_dietary_tags",
    )
    op.drop_index(
        op.f("ix_food_cuisine_tags_cuisine_tag_id"),
        table_name="food_cuisine_tags",
    )
    op.drop_index(
        op.f("ix_food_regions_region_id"),
        table_name="food_regions",
    )
    op.drop_index(
        op.f("ix_user_sessions_expires_at"),
        table_name="user_sessions",
    )
