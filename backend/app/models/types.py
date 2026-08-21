from sqlalchemy import Enum as SAEnum

from app.models.enums import (
    ActivityLevel,
    DietaryTagKind,
    DietPattern,
    FitnessGoal,
    FoodPreferenceType,
    FoodSourceLicense,
    MealPlanStatus,
    MealType,
    Sex,
    UnitDimension,
    UnitSystem,
    VerificationStatus,
)


def _sa_enum(enum_cls: type, name: str) -> SAEnum:
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        values_callable=lambda members: [item.value for item in members],
    )


UNIT_SYSTEM_ENUM = _sa_enum(UnitSystem, "unit_system")
UNIT_DIMENSION_ENUM = _sa_enum(UnitDimension, "unit_dimension")
SEX_ENUM = _sa_enum(Sex, "sex")
ACTIVITY_LEVEL_ENUM = _sa_enum(ActivityLevel, "activity_level")
FITNESS_GOAL_ENUM = _sa_enum(FitnessGoal, "fitness_goal")
DIET_PATTERN_ENUM = _sa_enum(DietPattern, "diet_pattern")
MEAL_TYPE_ENUM = _sa_enum(MealType, "meal_type")
MEAL_PLAN_STATUS_ENUM = _sa_enum(MealPlanStatus, "meal_plan_status")
FOOD_PREFERENCE_TYPE_ENUM = _sa_enum(FoodPreferenceType, "food_preference_type")
DIETARY_TAG_KIND_ENUM = _sa_enum(DietaryTagKind, "dietary_tag_kind")
FOOD_SOURCE_LICENSE_ENUM = _sa_enum(FoodSourceLicense, "food_source_license")
VERIFICATION_STATUS_ENUM = _sa_enum(VerificationStatus, "verification_status")
