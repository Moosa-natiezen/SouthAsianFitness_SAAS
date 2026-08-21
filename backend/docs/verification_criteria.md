# Food Dataset Verification Criteria

## Verification Statuses

| Status | Meaning | Can be imported to production? |
|--------|---------|-------------------------------|
| `verified` | Source confirmed, nutrition values pass plausibility checks, FDC ID matches expected | ✅ Yes |
| `verified_with_notes` | Source confirmed but has known approximations or minor deviations documented | ✅ Yes (with notes) |
| `pending_review` | Awaiting human verification; may have FDC ID mismatches, Atwater warnings, or missing source data | ❌ No |
| `rejected` | Failed verification; data is unreliable or contradicts authoritative sources | ❌ No |

## How Foods Move Between Statuses

### pending_review → verified

A food can move from `pending_review` to `verified` when ALL of the following are true:

1. **Source is confirmed**: The FDC ID (or other source identifier) matches the expected food
2. **Nutrition plausibility**: Atwater cross-check passes (deviation < 30% unless in exceptions list)
3. **No FDC ID mismatches**: The source identifier corresponds to the correct food
4. **Country assignments are justified**: The food is commonly consumed in the assigned countries
5. **Human review confirms**: A reviewer has verified the record against the source

### pending_review → verified_with_notes

A food can move to `verified_with_notes` when:

1. The source is confirmed but uses an **approximation** (e.g., caraway data for carom seeds)
2. Atwater deviation is between 30-80% and the exception is documented
3. The food uses **base ingredient data** for a prepared dish (no lab-analyzed values available)

### Any status → rejected

A food should be rejected when:

1. The FDC ID points to a completely different food
2. Nutrition values are physically impossible (e.g., >1000 kcal/100g for a non-oil food)
3. The source cannot be verified
4. The food is a duplicate of another verified record

## Plausibility Checks

### Atwater Cross-Check

```
calculated_kcal = (protein_g × 4) + (carbs_g × 4) + (fat_g × 9)
deviation = |stated_kcal - calculated_kcal| / calculated_kcal × 100
```

| Deviation | Action |
|-----------|--------|
| < 30% | ✅ Pass |
| 30-50% | ⚠️ Warning (document reason) |
| 50-80% | 🔍 Review required |
| > 80% | ❌ Suspicious (unless in exceptions) |

### Expected Atwater Exceptions

These foods legitimately deviate from Atwater calculations:

- **Coffee/Tea**: Contains methylxanthines and polyphenols not captured by macros
- **Pure oils/fats**: 0 protein/carbs, only fat; Atwater gives 900 kcal but actual is 884-900
- **Salt/Spices**: Negligible macros but may have trace calories

### Maximum Values

| Nutrient | Max per 100g | Reason |
|----------|--------------|--------|
| Calories | 1000 kcal | Only pure fats approach this |
| Protein | 100g | Impossible for any real food |
| Carbs | 100g | Impossible for any real food |
| Fat | 100g | Only pure oils |
| Sodium | 10,000 mg | Only salt exceeds this |

## FDC ID Verification

When a food's FDC ID is in the verified list, the record can be marked `verified`. When the FDC ID is:
- **Missing**: Record stays `pending_review`
- **Mismatches expected**: Record stays `pending_review` with note
- **Points to wrong food**: Record should be `rejected`

## Production Import Rules

The import pipeline MUST enforce:

1. **Only `verified` and `verified_with_notes` foods** may be imported to production
2. **`pending_review` foods are excluded** from production imports
3. **`rejected` foods are never imported**
4. **No silent overwrites**: Re-importing the same slug skips the existing record
5. **Provenance is preserved**: Every food must retain its source link

## Country Assignment Rules

Foods are assigned to countries based on:

1. **USDA SR Legacy coverage**: Many ingredients are universal
2. **South Asian cuisine relevance**: Foods commonly used in that country's cuisine
3. **No exclusivity assumption**: A food being common in India does NOT mean it's absent from Pakistan

Valid country codes: `PK`, `IN`, `BD`, `LK`, `NP`

## Coffee Anomaly Resolution

**Issue**: Coffee (brewed) reported 152% Atwater deviation

**Root cause**: Coffee contains 2 kcal per 100g from methylxanthines (caffeine, theobromine) and trace organic compounds. The Atwater system only accounts for protein, carbs, and fat. With P=0.12g, C=0g, F=0g, the Atwater estimate is 0.48 kcal, giving a 317% deviation.

**Resolution**: Coffee is added to the `ATWATER_EXCEPTIONS` list. The 152% figure is a legitimate data characteristic, not a data quality issue. The deviation is expected for beverages containing non-macronutrient calorie sources.

**Regression test**: `test_coffee_is_exception` in `test_dataset_audit.py` ensures this exception remains documented.
