import enum


class UnitSystem(str, enum.Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"


class Sex(str, enum.Enum):
    FEMALE = "female"
    MALE = "male"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class ActivityLevel(str, enum.Enum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTRA_ACTIVE = "extra_active"


class FitnessGoal(str, enum.Enum):
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    MUSCLE_BUILDING = "muscle_building"
    GENERAL_FITNESS = "general_fitness"


class DietPattern(str, enum.Enum):
    OMNIVORE = "omnivore"
    VEGETARIAN = "vegetarian"
    EGGETARIAN = "eggetarian"
    VEGAN = "vegan"
    PESCETARIAN = "pescetarian"


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class MealPlanStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FoodPreferenceType(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"


class DietaryTagKind(str, enum.Enum):
    DIET_PATTERN = "diet_pattern"
    RESTRICTION = "restriction"
    ALLERGEN = "allergen"


class UnitDimension(str, enum.Enum):
    MASS = "mass"
    VOLUME = "volume"
    COUNT = "count"
    ENERGY = "energy"
    LENGTH = "length"
