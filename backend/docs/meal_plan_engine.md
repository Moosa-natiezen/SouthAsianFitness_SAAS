# Meal Plan Generation & Optimization Engine

Deterministic, testable service that produces realistic, affordable South Asian meal plans matching a user's nutrition targets, budget, preferences, and restrictions.

## Architecture

```
POST /api/meal-plans/generate
        │
        ▼
┌─────────────────────────────────────────┐
│       meal_plan_service.py              │
│  (orchestrator: resolves profile,       │
│   nutrition targets, budget, filters)   │
└────────┬──────────────┬─────────────────┘
         │              │
    ┌────▼────┐    ┌────▼──────────────┐
    │nutrition│    │food_candidate_     │
    │_service │    │service             │
    └─────────┘    │(diet, allergens,   │
                   │ verified foods)    │
                   └────┬───────────────┘
                        │
                   ┌────▼──────────────┐
                   │meal_optimizer      │
                   │(greedy scoring     │
                   │ per meal slot)     │
                   └───────────────────┘
```

## Optimization Methodology

The optimizer uses a **greedy scoring approach** (not brute-force combinatorial):

1. **Candidate filtering**: Only verified/eligible foods pass through diet, allergy, and restriction filters.
2. **Per-slot scoring**: For each meal slot, candidates are scored against the slot's calorie/macro target using a weighted cost function.
3. **Greedy selection**: The best-scoring food is selected, then remaining targets are updated for the next food in the same slot.
4. **Portion optimization**: For each selected food, a coarse-to-fine grid search finds the portion that best fills remaining targets.

### Scoring Weights (configurable in `meal_plan_config.py`)

| Term | Weight | Description |
|---|---|---|
| Calorie deviation | 0.35 | How well the food's calories match the slot target |
| Protein deviation | 0.20 | How well protein matches |
| Carb deviation | 0.15 | How well carbs match |
| Fat deviation | 0.10 | How well fat matches |
| Budget deviation | 0.10 | Whether the food fits the budget |
| Variety penalty | 0.05 | Penalty for repeating foods/categories |
| Preference penalty | 0.05 | Penalty for disliked foods, bonus for liked |

Lower score = better food selection. All terms are normalized to [0, 1] before weighting.

## Portion Boundaries

Configurable in `PORTION_BOUNDS`:

| Food | Max (grams) |
|---|---|
| Rice | 400 |
| Roti/Chapati | 200 (~3 rotis) |
| Chicken | 300 |
| Beef/Mutton | 250 |
| Oil/Ghee | 30 |
| Egg | 150 (~3 eggs) |
| Yogurt | 300 |
| Default | 500 |

If a target cannot be reached within these bounds, a warning is emitted rather than forcing unrealistic portions.

## Meal Structure

Default daily structure (configurable):

| Meal | Calorie % | Min Foods | Max Foods |
|---|---|---|---|
| Breakfast | 25% | 1 | 2 |
| Lunch | 35% | 2 | 3 |
| Snack | 10% | 1 | 2 |
| Dinner | 30% | 2 | 3 |

Users can request 1–6 meals per day; the structure adjusts automatically.

## Budget Handling

- Daily budget is divided across meals proportionally to calorie fractions
- Region-level pricing preferred over country-level
- Missing prices allow inclusion but emit warnings
- No prices are invented

## Food Eligibility

**Included:** `verified`, `verified_with_notes`
**Excluded:** `pending_review`, `rejected`, `unverified`, `conflict`, `retracted`

Additional exclusions:
- Foods violating diet pattern (e.g., meat for vegetarians)
- Foods matching user allergens (dietary tags with kind=ALLERGEN)
- Foods matching user restrictions (dietary tags with kind=RESTRICTION)
- Explicitly disliked foods

**Conservative rule:** If a restriction cannot be safely evaluated, the food is excluded.

## Variety Enforcement

- `max_same_food_per_day`: Maximum times the same food can appear across all meals (default: 2)
- Category diversity: Penalty for using the same food category multiple times
- Multi-day: Not enforced beyond daily variety (future enhancement)

## Failure Handling

If no valid plan can be generated, the service returns a structured failure with:
- `reason`: Human-readable explanation
- `conflict_details`: Specific constraint conflicts
- `suggestions`: Recommended actions

Failure cases:
- Plan length exceeds maximum (30 days)
- User profile incomplete
- No eligible foods after all filters applied

## Determinism

For the same:
- User profile and preferences
- Food dataset
- Pricing data
- Configuration

The optimizer produces the **same result** on every run. No randomness is introduced.

## API Endpoints

### POST `/api/meal-plans/generate`
Generate a new meal plan.

**Request:**
```json
{
  "plan_days": 7,
  "meal_count": 4
}
```

**Response (success):**
```json
{
  "plan_id": "...",
  "plan_name": "General Fitness Plan - 2000 kcal/day",
  "days": [...],
  "nutrition": {...},
  "budget": {...},
  "warnings": [...]
}
```

**Response (failure):**
```json
{
  "success": false,
  "reason": "Plan length exceeds maximum 30 days",
  "conflict_details": [],
  "suggestions": ["Reduce plan length"]
}
```

All endpoints require authentication. Nutrition targets are calculated server-side (not from client input).

## Performance

- Bounded candidate set (default: 500 foods max)
- Greedy algorithm: O(slots × candidates × portion_steps)
- Portion optimization: ~20 iterations per food (coarse + fine grid)
- Total: ~3,200 scoring operations for a 4-meal day
- Completes in <1 second for typical inputs

## Known Limitations

- Category-based diet filtering cannot catch composite dishes (e.g., palak-paneer is in "vegetables" but contains dairy)
- No inter-day variety optimization yet
- No recipe-style food combinations (e.g., roti+salan treated as separate foods)
- Pricing data sparse for South Asian prepared dishes
- Macro targets may not be perfectly hit due to food granularity
- No medical/clinical nutrition claims
