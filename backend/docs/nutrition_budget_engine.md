# Nutrition & Budget Calculation Engine

Deterministic, testable backend services that convert a user's profile, goal, activity level, and budget into nutrition targets and budget constraints.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  API Layer                       │
│  POST /api/nutrition/calculate                   │
│  GET  /api/nutrition/targets                     │
│  GET  /api/nutrition/budget                      │
│  GET  /api/nutrition/eligible-foods              │
└──────────┬──────────────────┬────────────────────┘
           │                  │
    ┌──────▼──────┐    ┌──────▼──────┐
    │  Nutrition   │    │   Budget    │
    │   Service    │    │   Service   │
    └──────┬──────┘    └──────┬──────┘
           │                  │
    ┌──────▼──────┐    ┌──────▼──────┐
    │  Nutrition   │    │ Food Price  │
    │   Config     │    │   Data      │
    └─────────────┘    └─────────────┘
```

## Nutrition Formulas

### BMR — Mifflin-St Jeor (1990)

The Basal Metabolic Rate is calculated using the Mifflin-St Jeor equation, which is widely regarded as one of the most accurate BMR formulas for the general population.

- **Male:** BMR = 10 × weight_kg + 6.25 × height_cm − 5 × age − 5
- **Female:** BMR = 10 × weight_kg + 6.25 × height_cm − 5 × age − 161
- **Other/Prefer-not-to-say:** Average of male and female formulas

### TDEE — Total Daily Energy Expenditure

TDEE = BMR × Activity Multiplier (Harris-Benedict revised)

| Activity Level | Multiplier |
|---|---|
| Sedentary | 1.20 |
| Lightly Active | 1.375 |
| Moderately Active | 1.55 |
| Very Active | 1.725 |
| Extra Active | 1.90 |

### Goal Adjustments

| Goal | Daily Calorie Adjustment |
|---|---|
| Weight Loss | −500 kcal |
| Weight Gain | +400 kcal |
| Muscle Building | +300 kcal |
| General Fitness | 0 kcal |

### Safety Bounds

| Parameter | Min | Max |
|---|---|---|
| Age | 14 | 100 |
| Height | 100 cm | 250 cm |
| Weight | 30 kg | 300 kg |
| Calorie target | 1,000 kcal | 6,000 kcal |
| Calorie adjustment | −1,500 kcal | +1,500 kcal |

If a calculated target falls outside the safety bounds, it is **clamped** to the bound and the user receives a warning. The `is_bounded` flag is set to `true`.

### Macronutrients

Macros are calculated goal-aware:

1. **Protein:** Goal-specific g per kg body weight (midpoint of range):
   - Weight loss: 1.6–2.2 g/kg
   - Weight gain: 1.4–1.8 g/kg
   - Muscle building: 1.8–2.4 g/kg
   - General fitness: 1.2–1.6 g/kg

2. **Fat:** Goal-specific fraction of total calories (midpoint):
   - Weight loss: 20–35%
   - Weight gain: 20–35%
   - Muscle building: 20–30%
   - General fitness: 20–35%

3. **Carbohydrates:** Fill the remaining calorie allocation.

**Caloric values:**
- Protein: 4 kcal/g
- Carbohydrates: 4 kcal/g
- Fat: 9 kcal/g

If protein + fat calories exceed the total target, fat is reduced and a warning is emitted.

## Budget Engine

### Normalization

Budget periods are normalized to daily amounts:

| Period | Conversion |
|---|---|
| Daily | ÷ 1 |
| Weekly | ÷ 7 |
| Monthly | ÷ 30 |
| Yearly | ÷ 365 |

### Location-Aware Pricing

When querying food prices, the engine:
1. Prefers **region-level** pricing when available
2. Falls back to **country-level** pricing
3. Gracefully handles missing price data

### Meal Budget Check

The `check_meal_budget` function verifies whether a meal's estimated cost fits within the user's daily or weekly budget.

## Verified Food Filter

Only foods with these verification statuses may be used in calculations:
- `verified`
- `verified_with_notes`

Foods with these statuses are **excluded**:
- `unverified`
- `pending_review`
- `conflict`
- `retracted`
- `rejected`

This filter is enforced at the service layer. No pending-review or rejected data can enter the calculation pipeline.

## API Endpoints

All endpoints require authentication.

### POST `/api/nutrition/calculate`
Calculate combined nutrition + budget targets. Accepts optional profile overrides.

### GET `/api/nutrition/targets`
Get nutrition targets from the user's saved profile.

### GET `/api/nutrition/budget`
Get budget targets from the user's saved preferences.

### GET `/api/nutrition/eligible-foods`
Get a count of verified foods eligible for meal planning.

## Configuration

All magic numbers, formulas, and safety bounds are centralized in:
- `app/services/nutrition_config.py`

## Known Limitations

- This engine provides **estimates**, not medical prescriptions
- BMR formulas have ±10% accuracy for most populations
- South Asian populations may have different body composition norms (this is not yet accounted for)
- No food-specific pricing data is included yet — the budget engine uses user-provided budget amounts
- Macro calculations assume average protein/fat ranges; individual optimization requires professional guidance
