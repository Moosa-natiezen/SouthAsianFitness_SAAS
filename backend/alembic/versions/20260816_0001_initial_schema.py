"""Initial database schema for South Asian Fitness SaaS

Revision ID: 20260816_0001
Revises:
Create Date: 2026-08-16 15:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260816_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Currencies
    op.create_table(
        "currencies",
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("symbol", sa.String(length=8), nullable=False),
        sa.Column("minor_units", sa.Integer(), nullable=False, server_default="2"),
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
        sa.PrimaryKeyConstraint("code", name=op.f("pk_currencies")),
    )

    # 2. Units
    op.create_table(
        "units",
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "dimension",
            sa.Enum(
                "mass",
                "volume",
                "count",
                "energy",
                "length",
                name="unit_dimension",
            ),
            nullable=False,
        ),
        sa.Column("to_base_factor", sa.Numeric(precision=18, scale=8), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_units")),
        sa.UniqueConstraint("code", name=op.f("uq_units_code")),
    )

    # 3. Countries
    op.create_table(
        "countries",
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("iso_code", sa.String(length=2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column(
            "default_unit_system",
            sa.Enum("metric", "imperial", name="unit_system"),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(
            ["currency_code"],
            ["currencies.code"],
            name=op.f("fk_countries_currency_code_currencies"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_countries")),
        sa.UniqueConstraint("iso_code", name=op.f("uq_countries_iso_code")),
    )
    op.create_index(
        op.f("ix_countries_currency_code"),
        "countries",
        ["currency_code"],
        unique=False,
    )

    # 4. Regions
    op.create_table(
        "regions",
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=True),
        sa.Column("country_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["country_id"],
            ["countries.id"],
            name=op.f("fk_regions_country_id_countries"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_regions")),
        sa.UniqueConstraint(
            "country_id", "code", name=op.f("uq_regions_country_id_code")
        ),
        sa.UniqueConstraint(
            "country_id", "name", name=op.f("uq_regions_country_id_name")
        ),
    )
    op.create_index(
        op.f("ix_regions_country_id"), "regions", ["country_id"], unique=False
    )

    # 5. Food Categories
    op.create_table(
        "food_categories",
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_food_categories")),
        sa.UniqueConstraint("slug", name=op.f("uq_food_categories_slug")),
    )

    # 6. Cuisine Tags
    op.create_table(
        "cuisine_tags",
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cuisine_tags")),
        sa.UniqueConstraint("slug", name=op.f("uq_cuisine_tags_slug")),
    )

    # 7. Dietary Tags
    op.create_table(
        "dietary_tags",
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "diet_pattern",
                "restriction",
                "allergen",
                name="dietary_tag_kind",
            ),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dietary_tags")),
        sa.UniqueConstraint("slug", name=op.f("uq_dietary_tags_slug")),
    )
    op.create_index(
        op.f("ix_dietary_tags_kind"), "dietary_tags", ["kind"], unique=False
    )

    # 8. Foods
    op.create_table(
        "foods",
        sa.Column("slug", sa.String(length=150), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "translations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("serving_size", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("serving_unit_id", sa.Uuid(), nullable=False),
        sa.Column(
            "grams_per_serving", sa.Numeric(precision=10, scale=3), nullable=True
        ),
        sa.Column("calories", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("protein_g", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("carbs_g", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("fat_g", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("fiber_g", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column("sugar_g", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column("sodium_mg", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.CheckConstraint(
            "calories >= 0", name=op.f("ck_foods_non_negative_calories")
        ),
        sa.CheckConstraint(
            "serving_size > 0", name=op.f("ck_foods_positive_serving_size")
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["food_categories.id"],
            name=op.f("fk_foods_category_id_food_categories"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["serving_unit_id"],
            ["units.id"],
            name=op.f("fk_foods_serving_unit_id_units"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_foods")),
        sa.UniqueConstraint("slug", name=op.f("uq_foods_slug")),
    )
    op.create_index(
        op.f("ix_foods_category_id"), "foods", ["category_id"], unique=False
    )
    op.create_index(op.f("ix_foods_name"), "foods", ["name"], unique=False)
    op.create_index(
        op.f("ix_foods_serving_unit_id"),
        "foods",
        ["serving_unit_id"],
        unique=False,
    )

    # 9. Food Ingredients
    op.create_table(
        "food_ingredients",
        sa.Column("parent_food_id", sa.Uuid(), nullable=False),
        sa.Column("ingredient_food_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.Column("notes", sa.String(length=255), nullable=True),
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
        sa.CheckConstraint(
            "quantity > 0",
            name=op.f("ck_food_ingredients_positive_ingredient_quantity"),
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_food_id"],
            ["foods.id"],
            name=op.f("fk_food_ingredients_ingredient_food_id_foods"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["parent_food_id"],
            ["foods.id"],
            name=op.f("fk_food_ingredients_parent_food_id_foods"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["unit_id"],
            ["units.id"],
            name=op.f("fk_food_ingredients_unit_id_units"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_food_ingredients")),
        sa.UniqueConstraint(
            "parent_food_id",
            "ingredient_food_id",
            name=op.f("uq_food_ingredients_parent_ingredient"),
        ),
    )
    op.create_index(
        op.f("ix_food_ingredients_ingredient_food_id"),
        "food_ingredients",
        ["ingredient_food_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_food_ingredients_parent_food_id"),
        "food_ingredients",
        ["parent_food_id"],
        unique=False,
    )

    # 10. Food Prices
    op.create_table(
        "food_prices",
        sa.Column("food_id", sa.Uuid(), nullable=False),
        sa.Column("country_id", sa.Uuid(), nullable=False),
        sa.Column("region_id", sa.Uuid(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.CheckConstraint(
            "amount >= 0", name=op.f("ck_food_prices_non_negative_price")
        ),
        sa.CheckConstraint(
            "quantity > 0", name=op.f("ck_food_prices_positive_price_quantity")
        ),
        sa.ForeignKeyConstraint(
            ["country_id"],
            ["countries.id"],
            name=op.f("fk_food_prices_country_id_countries"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["currency_code"],
            ["currencies.code"],
            name=op.f("fk_food_prices_currency_code_currencies"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_food_prices_food_id_foods"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["region_id"],
            ["regions.id"],
            name=op.f("fk_food_prices_region_id_regions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["unit_id"],
            ["units.id"],
            name=op.f("fk_food_prices_unit_id_units"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_food_prices")),
    )
    op.create_index(
        op.f("ix_food_prices_country_id"),
        "food_prices",
        ["country_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_food_prices_currency_code"),
        "food_prices",
        ["currency_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_food_prices_food_id"),
        "food_prices",
        ["food_id"],
        unique=False,
    )
    op.create_index(
        "ix_food_prices_lookup",
        "food_prices",
        ["food_id", "country_id", "region_id", "observed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_food_prices_region_id"),
        "food_prices",
        ["region_id"],
        unique=False,
    )

    # 11. Food Association Tables
    op.create_table(
        "food_cuisine_tags",
        sa.Column("food_id", sa.Uuid(), nullable=False),
        sa.Column("cuisine_tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["cuisine_tag_id"],
            ["cuisine_tags.id"],
            name=op.f("fk_food_cuisine_tags_cuisine_tag_id_cuisine_tags"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_food_cuisine_tags_food_id_foods"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "food_id", "cuisine_tag_id", name=op.f("pk_food_cuisine_tags")
        ),
    )

    op.create_table(
        "food_dietary_tags",
        sa.Column("food_id", sa.Uuid(), nullable=False),
        sa.Column("dietary_tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dietary_tag_id"],
            ["dietary_tags.id"],
            name=op.f("fk_food_dietary_tags_dietary_tag_id_dietary_tags"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_food_dietary_tags_food_id_foods"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "food_id", "dietary_tag_id", name=op.f("pk_food_dietary_tags")
        ),
    )

    op.create_table(
        "food_regions",
        sa.Column("food_id", sa.Uuid(), nullable=False),
        sa.Column("region_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_food_regions_food_id_foods"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["region_id"],
            ["regions.id"],
            name=op.f("fk_food_regions_region_id_regions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "food_id", "region_id", name=op.f("pk_food_regions")
        ),
    )

    # 12. Meals
    op.create_table(
        "meals",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "translations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "meal_type",
            sa.Enum(
                "breakfast",
                "lunch",
                "dinner",
                "snack",
                name="meal_type",
            ),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meals")),
    )
    op.create_index(
        op.f("ix_meals_meal_type"), "meals", ["meal_type"], unique=False
    )
    op.create_index(op.f("ix_meals_name"), "meals", ["name"], unique=False)

    # 13. Meal Foods
    op.create_table(
        "meal_foods",
        sa.Column("meal_id", sa.Uuid(), nullable=False),
        sa.Column("food_id", sa.Uuid(), nullable=False),
        sa.Column("servings", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("serving_unit_id", sa.Uuid(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
        sa.CheckConstraint(
            "servings > 0", name=op.f("ck_meal_foods_positive_meal_servings")
        ),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_meal_foods_food_id_foods"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["meal_id"],
            ["meals.id"],
            name=op.f("fk_meal_foods_meal_id_meals"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["serving_unit_id"],
            ["units.id"],
            name=op.f("fk_meal_foods_serving_unit_id_units"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meal_foods")),
        sa.UniqueConstraint(
            "meal_id",
            "food_id",
            "sort_order",
            name=op.f("uq_meal_foods_meal_food_order"),
        ),
    )
    op.create_index(
        op.f("ix_meal_foods_food_id"), "meal_foods", ["food_id"], unique=False
    )
    op.create_index(
        op.f("ix_meal_foods_meal_id"), "meal_foods", ["meal_id"], unique=False
    )

    # 14. Users
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("country_id", sa.Uuid(), nullable=False),
        sa.Column("region_id", sa.Uuid(), nullable=True),
        sa.Column(
            "preferred_language",
            sa.String(length=16),
            nullable=False,
            server_default="en",
        ),
        sa.Column(
            "preferred_unit_system",
            sa.Enum("metric", "imperial", name="unit_system"),
            nullable=False,
        ),
        sa.Column("preferred_currency_code", sa.String(length=3), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.ForeignKeyConstraint(
            ["country_id"],
            ["countries.id"],
            name=op.f("fk_users_country_id_countries"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["preferred_currency_code"],
            ["currencies.code"],
            name=op.f("fk_users_preferred_currency_code_currencies"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["region_id"],
            ["regions.id"],
            name=op.f("fk_users_region_id_regions"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(
        op.f("ix_users_country_id"), "users", ["country_id"], unique=False
    )
    op.create_index(
        op.f("ix_users_preferred_currency_code"),
        "users",
        ["preferred_currency_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_users_region_id"), "users", ["region_id"], unique=False
    )

    # 15. User Profiles
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("age_years", sa.Integer(), nullable=False),
        sa.Column(
            "sex",
            sa.Enum("female", "male", "other", "prefer_not_to_say", name="sex"),
            nullable=False,
        ),
        sa.Column("height_cm", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column(
            "activity_level",
            sa.Enum(
                "sedentary",
                "lightly_active",
                "moderately_active",
                "very_active",
                "extra_active",
                name="activity_level",
            ),
            nullable=False,
        ),
        sa.Column(
            "fitness_goal",
            sa.Enum(
                "weight_loss",
                "weight_gain",
                "muscle_building",
                "general_fitness",
                name="fitness_goal",
            ),
            nullable=False,
        ),
        sa.Column(
            "diet_pattern",
            sa.Enum(
                "omnivore",
                "vegetarian",
                "eggetarian",
                "vegan",
                "pescetarian",
                name="diet_pattern",
            ),
            nullable=False,
        ),
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
        sa.CheckConstraint(
            "age_years > 0", name=op.f("ck_user_profiles_positive_age")
        ),
        sa.CheckConstraint(
            "height_cm > 0", name=op.f("ck_user_profiles_positive_height")
        ),
        sa.CheckConstraint(
            "weight_kg > 0", name=op.f("ck_user_profiles_positive_weight")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_profiles")),
        sa.UniqueConstraint("user_id", name=op.f("uq_user_profiles_user_id")),
    )

    # 16. User Profile Dietary Tags
    op.create_table(
        "user_profile_dietary_tags",
        sa.Column("user_profile_id", sa.Uuid(), nullable=False),
        sa.Column("dietary_tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dietary_tag_id"],
            ["dietary_tags.id"],
            name=op.f(
                "fk_user_profile_dietary_tags_dietary_tag_id_dietary_tags"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_profile_id"],
            ["user_profiles.id"],
            name=op.f(
                "fk_user_profile_dietary_tags_user_profile_id_user_profiles"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_profile_id",
            "dietary_tag_id",
            name=op.f("pk_user_profile_dietary_tags"),
        ),
    )

    # 17. User Preferences
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "weekly_budget_amount",
            sa.Numeric(precision=14, scale=4),
            nullable=True,
        ),
        sa.Column(
            "budget_currency_code", sa.String(length=3), nullable=True
        ),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.CheckConstraint(
            "weekly_budget_amount IS NULL OR weekly_budget_amount >= 0",
            name=op.f("ck_user_preferences_non_negative_weekly_budget"),
        ),
        sa.ForeignKeyConstraint(
            ["budget_currency_code"],
            ["currencies.code"],
            name=op.f(
                "fk_user_preferences_budget_currency_code_currencies"
            ),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_preferences_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_preferences")),
        sa.UniqueConstraint("user_id", name=op.f("uq_user_preferences_user_id")),
    )

    # 18. User Preferences Associations
    op.create_table(
        "user_preference_cuisine_tags",
        sa.Column("user_preferences_id", sa.Uuid(), nullable=False),
        sa.Column("cuisine_tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["cuisine_tag_id"],
            ["cuisine_tags.id"],
            name=op.f(
                "fk_user_preference_cuisine_tags_cuisine_tag_id_cuisine_tags"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_preferences_id"],
            ["user_preferences.id"],
            name=op.f(
                "fk_user_preference_cuisine_tags_user_preferences_id_user_preferences"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_preferences_id",
            "cuisine_tag_id",
            name=op.f("pk_user_preference_cuisine_tags"),
        ),
    )

    op.create_table(
        "user_preference_dietary_tags",
        sa.Column("user_preferences_id", sa.Uuid(), nullable=False),
        sa.Column("dietary_tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dietary_tag_id"],
            ["dietary_tags.id"],
            name=op.f(
                "fk_user_preference_dietary_tags_dietary_tag_id_dietary_tags"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_preferences_id"],
            ["user_preferences.id"],
            name=op.f(
                "fk_user_preference_dietary_tags_user_preferences_id_user_preferences"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_preferences_id",
            "dietary_tag_id",
            name=op.f("pk_user_preference_dietary_tags"),
        ),
    )

    op.create_table(
        "user_preference_regions",
        sa.Column("user_preferences_id", sa.Uuid(), nullable=False),
        sa.Column("region_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["region_id"],
            ["regions.id"],
            name=op.f("fk_user_preference_regions_region_id_regions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_preferences_id"],
            ["user_preferences.id"],
            name=op.f(
                "fk_user_preference_regions_user_preferences_id_user_preferences"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_preferences_id",
            "region_id",
            name=op.f("pk_user_preference_regions"),
        ),
    )

    # 19. User Food Preferences
    op.create_table(
        "user_food_preferences",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("food_id", sa.Uuid(), nullable=False),
        sa.Column(
            "preference_type",
            sa.Enum("like", "dislike", name="food_preference_type"),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_user_food_preferences_food_id_foods"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_food_preferences_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_food_preferences")),
        sa.UniqueConstraint(
            "user_id",
            "food_id",
            name=op.f("uq_user_food_preferences_user_food"),
        ),
    )
    op.create_index(
        op.f("ix_user_food_preferences_food_id"),
        "user_food_preferences",
        ["food_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_food_preferences_user_id"),
        "user_food_preferences",
        ["user_id"],
        unique=False,
    )

    # 20. Meal Plans
    op.create_table(
        "meal_plans",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column(
            "goal",
            sa.Enum(
                "weight_loss",
                "weight_gain",
                "muscle_building",
                "general_fitness",
                name="fitness_goal",
            ),
            nullable=False,
        ),
        sa.Column(
            "daily_calorie_target",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column(
            "daily_protein_g", sa.Numeric(precision=10, scale=3), nullable=True
        ),
        sa.Column(
            "daily_carbs_g", sa.Numeric(precision=10, scale=3), nullable=True
        ),
        sa.Column("daily_fat_g", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column(
            "daily_budget_amount",
            sa.Numeric(precision=14, scale=4),
            nullable=True,
        ),
        sa.Column(
            "budget_currency_code", sa.String(length=3), nullable=True
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "active",
                "completed",
                "cancelled",
                name="meal_plan_status",
            ),
            nullable=False,
            server_default="draft",
        ),
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
        sa.CheckConstraint(
            "daily_budget_amount IS NULL OR daily_budget_amount >= 0",
            name=op.f("ck_meal_plans_non_negative_daily_budget"),
        ),
        sa.CheckConstraint(
            "daily_calorie_target > 0",
            name=op.f("ck_meal_plans_positive_calorie_target"),
        ),
        sa.CheckConstraint(
            "end_date >= start_date", name=op.f("ck_meal_plans_valid_plan_dates")
        ),
        sa.ForeignKeyConstraint(
            ["budget_currency_code"],
            ["currencies.code"],
            name=op.f("fk_meal_plans_budget_currency_code_currencies"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_meal_plans_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meal_plans")),
    )
    op.create_index(
        op.f("ix_meal_plans_status"), "meal_plans", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_meal_plans_user_id"), "meal_plans", ["user_id"], unique=False
    )
    op.create_index(
        "ix_meal_plans_user_status",
        "meal_plans",
        ["user_id", "status"],
        unique=False,
    )

    # 21. Meal Plan Days
    op.create_table(
        "meal_plan_days",
        sa.Column("meal_plan_id", sa.Uuid(), nullable=False),
        sa.Column("plan_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["meal_plan_id"],
            ["meal_plans.id"],
            name=op.f("fk_meal_plan_days_meal_plan_id_meal_plans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meal_plan_days")),
        sa.UniqueConstraint(
            "meal_plan_id",
            "plan_date",
            name=op.f("uq_meal_plan_days_plan_date"),
        ),
    )
    op.create_index(
        op.f("ix_meal_plan_days_meal_plan_id"),
        "meal_plan_days",
        ["meal_plan_id"],
        unique=False,
    )

    # 22. Meal Plan Day Meals
    op.create_table(
        "meal_plan_day_meals",
        sa.Column("meal_plan_day_id", sa.Uuid(), nullable=False),
        sa.Column("meal_id", sa.Uuid(), nullable=False),
        sa.Column(
            "meal_type",
            sa.Enum(
                "breakfast",
                "lunch",
                "dinner",
                "snack",
                name="meal_type",
            ),
            nullable=True,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(
            ["meal_id"],
            ["meals.id"],
            name=op.f("fk_meal_plan_day_meals_meal_id_meals"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["meal_plan_day_id"],
            ["meal_plan_days.id"],
            name=op.f("fk_meal_plan_day_meals_meal_plan_day_id_meal_plan_days"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meal_plan_day_meals")),
        sa.UniqueConstraint(
            "meal_plan_day_id",
            "meal_id",
            "sort_order",
            name=op.f("uq_meal_plan_day_meals_day_meal_order"),
        ),
    )
    op.create_index(
        op.f("ix_meal_plan_day_meals_meal_id"),
        "meal_plan_day_meals",
        ["meal_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_meal_plan_day_meals_meal_plan_day_id"),
        "meal_plan_day_meals",
        ["meal_plan_day_id"],
        unique=False,
    )

    # 23. Progress Entries
    op.create_table(
        "progress_entries",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("recorded_on", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("waist_cm", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("hip_cm", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column(
            "body_fat_percent", sa.Numeric(precision=5, scale=2), nullable=True
        ),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.CheckConstraint(
            "weight_kg > 0",
            name=op.f("ck_progress_entries_positive_progress_weight"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_progress_entries_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_progress_entries")),
        sa.UniqueConstraint(
            "user_id",
            "recorded_on",
            name=op.f("uq_progress_entries_user_recorded_on"),
        ),
    )
    op.create_index(
        op.f("ix_progress_entries_recorded_on"),
        "progress_entries",
        ["recorded_on"],
        unique=False,
    )
    op.create_index(
        op.f("ix_progress_entries_user_id"),
        "progress_entries",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop tables in reverse topological order
    op.drop_index(
        op.f("ix_progress_entries_user_id"), table_name="progress_entries"
    )
    op.drop_index(
        op.f("ix_progress_entries_recorded_on"), table_name="progress_entries"
    )
    op.drop_table("progress_entries")

    op.drop_index(
        op.f("ix_meal_plan_day_meals_meal_plan_day_id"),
        table_name="meal_plan_day_meals",
    )
    op.drop_index(
        op.f("ix_meal_plan_day_meals_meal_id"),
        table_name="meal_plan_day_meals",
    )
    op.drop_table("meal_plan_day_meals")

    op.drop_index(
        op.f("ix_meal_plan_days_meal_plan_id"), table_name="meal_plan_days"
    )
    op.drop_table("meal_plan_days")

    op.drop_index("ix_meal_plans_user_status", table_name="meal_plans")
    op.drop_index(op.f("ix_meal_plans_user_id"), table_name="meal_plans")
    op.drop_index(op.f("ix_meal_plans_status"), table_name="meal_plans")
    op.drop_table("meal_plans")

    op.drop_index(
        op.f("ix_user_food_preferences_user_id"),
        table_name="user_food_preferences",
    )
    op.drop_index(
        op.f("ix_user_food_preferences_food_id"),
        table_name="user_food_preferences",
    )
    op.drop_table("user_food_preferences")

    op.drop_table("user_preference_regions")
    op.drop_table("user_preference_dietary_tags")
    op.drop_table("user_preference_cuisine_tags")
    op.drop_table("user_preferences")
    op.drop_table("user_profile_dietary_tags")
    op.drop_table("user_profiles")

    op.drop_index(op.f("ix_users_region_id"), table_name="users")
    op.drop_index(
        op.f("ix_users_preferred_currency_code"), table_name="users"
    )
    op.drop_index(op.f("ix_users_country_id"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_meal_foods_meal_id"), table_name="meal_foods")
    op.drop_index(op.f("ix_meal_foods_food_id"), table_name="meal_foods")
    op.drop_table("meal_foods")

    op.drop_index(op.f("ix_meals_name"), table_name="meals")
    op.drop_index(op.f("ix_meals_meal_type"), table_name="meals")
    op.drop_table("meals")

    op.drop_table("food_regions")
    op.drop_table("food_dietary_tags")
    op.drop_table("food_cuisine_tags")

    op.drop_index(op.f("ix_food_prices_region_id"), table_name="food_prices")
    op.drop_index("ix_food_prices_lookup", table_name="food_prices")
    op.drop_index(op.f("ix_food_prices_food_id"), table_name="food_prices")
    op.drop_index(
        op.f("ix_food_prices_currency_code"), table_name="food_prices"
    )
    op.drop_index(op.f("ix_food_prices_country_id"), table_name="food_prices")
    op.drop_table("food_prices")

    op.drop_index(
        op.f("ix_food_ingredients_parent_food_id"),
        table_name="food_ingredients",
    )
    op.drop_index(
        op.f("ix_food_ingredients_ingredient_food_id"),
        table_name="food_ingredients",
    )
    op.drop_table("food_ingredients")

    op.drop_index(
        op.f("ix_foods_serving_unit_id"), table_name="foods"
    )
    op.drop_index(op.f("ix_foods_name"), table_name="foods")
    op.drop_index(op.f("ix_foods_category_id"), table_name="foods")
    op.drop_table("foods")

    op.drop_index(op.f("ix_dietary_tags_kind"), table_name="dietary_tags")
    op.drop_table("dietary_tags")
    op.drop_table("cuisine_tags")
    op.drop_table("food_categories")

    op.drop_index(op.f("ix_regions_country_id"), table_name="regions")
    op.drop_table("regions")

    op.drop_index(
        op.f("ix_countries_currency_code"), table_name="countries"
    )
    op.drop_table("countries")

    op.drop_table("units")
    op.drop_table("currencies")

    # Drop PostgreSQL ENUM types
    sa.Enum(name="food_preference_type").drop(
        op.get_bind(), checkfirst=True
    )
    sa.Enum(name="meal_plan_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="fitness_goal").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="diet_pattern").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="activity_level").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="sex").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="meal_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="dietary_tag_kind").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="unit_system").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="unit_dimension").drop(op.get_bind(), checkfirst=True)
