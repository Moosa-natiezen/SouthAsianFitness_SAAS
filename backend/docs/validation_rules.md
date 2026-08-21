# Food Data Validation Rules

This document defines the validation rules enforced during food data import.
All rules are enforced at the schema layer (Pydantic) and the service layer
(SQLAlchemy + import service). Violations cause the entire batch to be rolled
back; partial imports are never committed.

---

## 1. Missing Nutrition Data

### Rule: Required macro-nutrients must be present

The following fields are **mandatory** for every food record:

- `calories` (≥ 0)
- `protein_g` (≥ 0)
- `carbs_g` (≥ 0)
- `fat_g` (≥ 0)

If any of these are missing, the record is **rejected**.

### Rule: Optional nutrients default to NULL

The following fields are optional:

- `fiber_g`
- `sugar_g`
- `sodium_mg`

NULL values are permitted and indicate the data was not available from the
source. This is preferred over guessing or interpolating.

### Rule: Nutrition cannot be all zeros

A food record where `calories`, `protein_g`, `carbs_g`, and `fat_g` are all
zero is flagged as a **warning** (not rejected, since some foods like plain
water or black coffee genuinely have near-zero nutrition). However, the import
summary should record a warning for such records.

---

## 2. Impossible Values

### Rule: Non-negative constraints

All nutrition values must be ≥ 0. Negative values are rejected at the schema
level.

### Rule: Maximum bounds

No single nutrition value may exceed 100,000. This prevents obviously corrupt
data (e.g., a food with 500,000 calories per 100g).

### Rule: Calorie-macro sanity check

The Atwater system estimates:

```
calories ≈ (protein_g × 4) + (carbs_g × 4) + (fat_g × 9)
```

**Validation**: If the stated `calories` deviates from the Atwater estimate
by more than **±30%**, the record is flagged as a **warning**.

Examples:
- `protein=10, carbs=10, fat=10` → Atwater = 40+40+90 = **170 kcal**
- If `calories` is listed as 500 → **warning** (deviation > 30%)
- If `calories` is listed as 160 → OK (within 30%)

This check is a **warning**, not a rejection, because:
- Fiber contributes some calories (~2 kcal/g) not captured by Atwater.
- Alcohol contributes ~7 kcal/g.
- Some foods have unusual macronutrient profiles.

### Rule: Carbohydrate + fiber consistency

If both `carbs_g` and `fiber_g` are provided, `fiber_g` should be ≤
`carbs_g`. Fiber is a subset of total carbohydrates. If `fiber_g` >
`carbs_g`, flag as a **warning**.

### Rule: Sodium bounds

Sodium values for most foods should be between 0 and 5,000 mg per 100g.
Values above 5,000 mg/100g are flagged as a **warning** (pure salt would be
~39,000 mg/100g, so extreme values suggest a unit error).

---

## 3. Inconsistent Macros / Calories

### Rule: Atwater cross-check

As described in section 2 above, the Atwater estimate is compared against the
stated calories. A deviation > 30% produces a warning.

### Rule: Fat calories consistency

Fat contributes 9 kcal/g. If `fat_g × 9` exceeds the stated `calories`
by more than 50%, flag as a **warning** (this is physically impossible for
a real food).

---

## 4. Invalid Serving Units

### Rule: Unit must exist in the units table

Every serving unit code must correspond to an entry in the `units` table.
Unknown unit codes trigger auto-creation using defaults, but only for
predefined codes (g, kg, ml, l, cup, tbsp, tsp, pc, piece, roti, serving).

If a unit code is not in the predefined set and not already in the database,
it is created with `dimension=COUNT` and `to_base_factor=NULL`.

### Rule: Positive serving amount

`serving.amount` must be > 0. Zero or negative serving amounts are rejected.

### Rule: Grams equivalent required for count/volume units

When the serving unit is `pc`, `piece`, `roti`, `serving`, `cup`, `tbsp`,
or `tsp`, a `grams_equivalent` value should be provided. If missing, a
**warning** is recorded, but the import is not rejected.

### Rule: Serving amount upper bound

`serving.amount` must be ≤ 100,000. This prevents obviously corrupt data.

---

## 5. Duplicate Foods

### Rule: Slug uniqueness

Foods are identified by their normalized slug. Within a single import batch,
duplicate slugs cause the **entire batch to be rejected**.

### Rule: Cross-batch deduplication

When importing a new dataset, foods with slugs that already exist in the
database are **skipped** (not overwritten, not duplicated). The import
summary reports the count of skipped records.

### Rule: Slug normalization

Slugs are normalized as follows:
1. Trim whitespace.
2. Convert to lowercase.
3. Replace spaces with hyphens.
4. Remove all characters except alphanumeric, hyphens, and underscores.
5. Strip leading/trailing hyphens.
6. If the result is empty, use the fallback `"food"`.

### Rule: Idempotent re-import

Re-importing the same dataset should produce:
- `imported = 0` (no new records)
- `skipped = N` (all existing records skipped)
- `failed = 0` (no errors)

---

## 6. Conflicting Sources

### Rule: Never silently overwrite

If a food already exists and a new import attempts to update it, the
existing record is **skipped**. The new data is NOT merged or overwritten.

### Rule: Conflict detection

When a food exists with `verification_status = 'verified'` and a new import
attempts to add data from a different source, the food is not modified. The
import summary records a warning indicating the conflict.

### Rule: Verification status transitions

The following transitions are allowed:

```
unverified → pending_review → verified
                              → conflict
unverified → conflict
verified → retracted (manual only)
conflict → verified (manual resolution only)
```

Automatic imports can only set: `unverified`, `pending_review`.
The `verified`, `conflict`, and `retracted` statuses require manual
human review.

---

## 7. Additional Validation Rules

### Rule: Name and slug required

Both `name` and `slug` are required and must be non-empty after trimming.

### Rule: Category required

Every food must have a `category` string. If the category doesn't exist,
it is auto-created.

### Rule: At least one country required

Every food must be associated with at least one country code. Records with
no country (neither `country` nor `countries` populated) are rejected.

### Rule: Country code format

Country codes must be exactly 2 uppercase letters (ISO 3166-1 alpha-2).

### Rule: Currency code format

Currency codes must be exactly 3 uppercase letters (ISO 4217).

### Rule: Price non-negative

Food prices must have `amount ≥ 0` and `quantity > 0`.

### Rule: Ingredient quantity positive

Ingredient quantities must be > 0.

### Rule: Ingredient self-reference prevention

An ingredient cannot reference its own parent food (prevents circular
composition).

---

## 8. Warning vs. Rejection Summary

| Condition | Severity | Action |
|-----------|----------|--------|
| Missing required macro-nutrients | **REJECT** | Record rejected, batch rolled back |
| Negative nutrition values | **REJECT** | Record rejected, batch rolled back |
| Duplicate slug in batch | **REJECT** | Entire batch rolled back |
| Missing country | **REJECT** | Record rejected, batch rolled back |
| Zero serving amount | **REJECT** | Record rejected, batch rolled back |
| Atwater deviation > 30% | **WARNING** | Record imported, warning logged |
| fiber > carbs | **WARNING** | Record imported, warning logged |
| Extreme sodium (> 5000mg) | **WARNING** | Record imported, warning logged |
| All macros zero | **WARNING** | Record imported, warning logged |
| Missing grams_equivalent for count unit | **WARNING** | Record imported, warning logged |
| Existing slug in database | **SKIP** | Record skipped, not imported |
| Unrecognized source (new) | **INFO** | New FoodSource record created |

---

## 9. Implementation Locations

| Rule | Schema Layer | Service Layer |
|------|-------------|---------------|
| Required fields | `FoodImportRecord` Pydantic model | `_upsert_food()` |
| Numeric bounds | `NutritionImport` field validators | — |
| Slug normalization | — | `_normalize_slug()` |
| Duplicate detection | `DatasetEnvelope` validator | `import_food_dataset()` |
| Atwater cross-check | — | `validate_nutrition_consistency()` (future) |
| Country validation | `FoodImportRecord` validator | `import_food_dataset()` |
| Source provenance | `SourceProvenanceImport` model | `_ensure_food_source()` |
