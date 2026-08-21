# South Asian Food Dataset — Coverage Summary

## Overview

| Metric | Value |
|--------|-------|
| Total foods | 198 |
| Ingredients | 169 |
| Composite dishes | 29 |
| Complete nutrition (cal+P+C+F > 0) | 172 |
| Incomplete nutrition | 26 (oils/fats/beverages with 0 protein/carbs) |
| All flagged for review | 198 (verification_status = pending_review) |
| Pydantic schema validation | PASSED (0 errors) |
| Duplicate slugs | 0 |

## Source

**USDA FoodData Central** — SR Legacy / Foundation datasets
- License: **CC0 1.0 Universal (Public Domain)**
- Attribution required: No (but recommended as good practice)
- Commercial use: **Permitted**
- Electronic redistribution: **Permitted**
- Raw data storage: **Permitted**
- Citation: U.S. Department of Agriculture, Agricultural Research Service. FoodData Central, 2019. fdc.nal.usda.gov.

**No other sources used.** All 198 foods come from a single authoritative, public-domain source with no licensing restrictions.

## Nutrition Completeness

- 172 foods have all core macros (calories, protein, carbs, fat) > 0
- 26 foods have 0 in some macros (correct for: oils/fats [0 protein/carbs], salt [0 everything], black tea [near-0], etc.)
- 1 Atwater deviation flagged: Coffee (brewed) — 152% deviation is expected for a beverage with negligible macros

## Foods by Category

| Category | Count |
|----------|-------|
| Vegetables | 33 |
| Spices & Condiments | 24 |
| Fruits | 21 |
| Grains & Cereals | 18 |
| Legumes & Pulses | 16 |
| Dairy | 13 |
| Nuts & Seeds | 13 |
| Prepared Dishes | 15 |
| Oils & Fats | 8 |
| Breads | 8 |
| Beverages | 8 |
| Fish & Seafood | 6 |
| Meats | 5 |
| Sweeteners | 3 |
| Eggs | 3 |
| Snacks | 2 |
| Poultry | 2 |

## Foods by Country

| Country | Foods | % of dataset |
|---------|-------|-------------|
| India (IN) | 196 | 99.0% |
| Pakistan (PK) | 145 | 73.2% |
| Bangladesh (BD) | 138 | 69.7% |
| Nepal (NP) | 94 | 47.5% |
| Sri Lanka (LK) | 63 | 31.8% |

Note: Most foods are relevant to multiple countries. India has the highest coverage because USDA SR Legacy has the best overlap with Indian food ingredients.

## Foods by Type

| Type | Count |
|------|-------|
| Ingredient (raw/base) | 169 |
| Composite (prepared) | 29 |

## Key Limitations

1. **All 198 foods use USDA data** — this is excellent for base ingredients but limited for South Asian-specific prepared dishes
2. **No country-specific food composition tables** (ICMR-NIN, PARC, etc.) have been imported yet — their licensing terms need verification
3. **All foods marked `pending_review`** — awaiting human verification against the original USDA database
4. **Breads and prepared dishes** use base ingredient values (flour, rice) rather than actual lab-analyzed values for the prepared dish
5. **India** has the highest country coverage (99%) due to USDA's overlap with Indian ingredients; Sri Lanka has the lowest (32%)

## Files Created

| File | Purpose |
|------|---------|
| `data/south_asian_foods.json` | The 198-food dataset in canonical import format |
| `data/south_asian_foods_validation.json` | Validation report |
| `scripts/generate_dataset.py` | Primary dataset generator (USDA values, no API calls) |
| `scripts/build_dataset.py` | API-based builder (for when API key is available) |
| `scripts/add_extra_foods.py` | Supplementary foods to reach ~200 |
| `docs/south_asian_foods_coverage.md` | This file |
| `docs/data_sources.md` | Source strategy documentation |
| `docs/food_data_spec.md` | Canonical food data specification |
| `docs/validation_rules.md` | Validation rule set |
| `docs/dataset_phasing.md` | Phasing plan for future expansion |

## Next Steps

1. **Verify USDA values** against the live FDC API (requires API key to avoid rate limits)
2. **Investigate ICMR-NIN IFCT 2017 licensing** for Indian prepared dishes
3. **Contact national food composition table publishers** in PK, BD, LK, NP for licensing terms
4. **Add more prepared dishes** from verified sources (biryani, salan, khichdi, etc.)
5. **Import into the database** using the existing import pipeline (requires DATABASE_URL)
6. **Human review** of all 198 records to confirm accuracy
