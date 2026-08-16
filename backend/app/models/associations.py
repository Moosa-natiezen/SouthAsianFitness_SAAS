from sqlalchemy import Column, ForeignKey, Table, Uuid

from app.db.base import Base

food_regions = Table(
    "food_regions",
    Base.metadata,
    Column(
        "food_id",
        Uuid(as_uuid=True),
        ForeignKey("foods.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "region_id",
        Uuid(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

food_cuisine_tags = Table(
    "food_cuisine_tags",
    Base.metadata,
    Column(
        "food_id",
        Uuid(as_uuid=True),
        ForeignKey("foods.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "cuisine_tag_id",
        Uuid(as_uuid=True),
        ForeignKey("cuisine_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

food_dietary_tags = Table(
    "food_dietary_tags",
    Base.metadata,
    Column(
        "food_id",
        Uuid(as_uuid=True),
        ForeignKey("foods.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "dietary_tag_id",
        Uuid(as_uuid=True),
        ForeignKey("dietary_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

user_profile_dietary_tags = Table(
    "user_profile_dietary_tags",
    Base.metadata,
    Column(
        "user_profile_id",
        Uuid(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "dietary_tag_id",
        Uuid(as_uuid=True),
        ForeignKey("dietary_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

user_preference_dietary_tags = Table(
    "user_preference_dietary_tags",
    Base.metadata,
    Column(
        "user_preferences_id",
        Uuid(as_uuid=True),
        ForeignKey("user_preferences.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "dietary_tag_id",
        Uuid(as_uuid=True),
        ForeignKey("dietary_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

user_preference_cuisine_tags = Table(
    "user_preference_cuisine_tags",
    Base.metadata,
    Column(
        "user_preferences_id",
        Uuid(as_uuid=True),
        ForeignKey("user_preferences.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "cuisine_tag_id",
        Uuid(as_uuid=True),
        ForeignKey("cuisine_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

user_preference_regions = Table(
    "user_preference_regions",
    Base.metadata,
    Column(
        "user_preferences_id",
        Uuid(as_uuid=True),
        ForeignKey("user_preferences.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "region_id",
        Uuid(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
