# Food import / seeding guide

This project uses a JSON dataset as the canonical import format because it preserves nested food metadata, ingredient relationships, prices, serving information, and **data provenance** without forcing a lossy flattening step.

## Canonical schema

```json
{
  "dataset_source": {
    "name": "USDA FoodData Central",
    "version": "SR Legacy / Foundation 2024",
    "reference_url": "https://fdc.nal.usda.gov/",
    "license_category": "public_domain",
    "attribution_text": "Data from USDA FoodData Central, Public Domain.",
    "can_store_raw_data": true,
    "can_store_derived_values": true,
    "source_date": "2024-06-01T00:00:00+00:00"
  },
  "foods": [
    {
      "name": "Chicken salan",
      "slug": "chicken-salan",
      "description": "Sample chicken curry dish",
      "food_type": "composite",
      "category": "prepared-meals",
      "country": "PK",
      "countries": ["PK", "IN"],
      "region": "Punjab",
      "regions": ["Punjab"],
      "nutrition": {
        "calories": 420,
        "protein_g": 32,
        "carbs_g": 18,
        "fat_g": 23,
        "fiber_g": 3
      },
      "serving": {
        "amount": 1,
        "unit": "serving",
        "grams_equivalent": 350
      },
      "ingredients": [
        {"name": "chicken", "quantity": 180, "unit": "g"},
        {"name": "onion", "quantity": 40, "unit": "g"}
      ],
      "source": {
        "source_name": "ICMR-NIN Indian Food Composition Tables",
        "source_identifier": "IFCT-2017-042",
        "source_version": "2017",
        "verification_status": "pending_review",
        "notes": "Values adjusted for home preparation"
      },
      "prices": [
        {
          "country": "PK",
          "region": "Punjab",
          "currency": "PKR",
          "amount": 540,
          "quantity": 1,
          "unit": "serving",
          "observed_at": "2026-08-01T00:00:00+00:00"
        }
      ]
    }
  ]
}
```

## Provenance fields

Every food can carry a `source` block that records where its nutrition data came from. If omitted, the dataset-level `dataset_source` block is used. See `docs/food_data_spec.md` for the full specification.

| Field | Description |
|-------|-------------|
| `source_name` | Name of the data source (e.g., "USDA FoodData Central") |
| `source_identifier` | Source-specific ID for this food (e.g., FDC ID, IFCT code) |
| `source_version` | Version of the source dataset used |
| `source_date` | Date of the source data |
| `verification_status` | One of: `unverified`, `pending_review`, `verified`, `conflict`, `retracted` |
| `notes` | Free-text notes about the source or any adjustments made |

## Import commands

- Validate dry-run:
  `uv run python -m app.scripts.import_foods data/sample_foods.json --dry-run`
- Real import:
  `uv run python -m app.scripts.import_foods data/sample_foods.json`

## Duplicate rules

- Foods are resolved by a normalized slug.
- Countries are matched by ISO code.
- Regions are matched within a country by name.
- Categories are matched by slug.
- Units are matched by lower-case code.
- Duplicate slugs inside a single dataset are rejected.
- Re-importing the same dataset is idempotent: an already loaded slug is skipped instead of creating a duplicate record.

## Validation and error handling

- Required fields such as name, slug, category, serving, and nutrition are enforced.
- Negative or invalid numeric values are rejected.
- Serving amounts, ingredient quantities, and prices must be positive.
- Invalid country or currency values are rejected before import commits.
- If a critical validation error occurs, the entire dataset is rolled back and no partial import is committed.
- Provenance metadata is validated (valid source_name, valid verification_status enum).
- See `docs/validation_rules.md` for the full validation rule set.

## Adding new foods

1. Add a record to the JSON file.
2. Use a stable slug.
3. Include nutrition and serving metadata.
4. Add ingredient relationships for composite dishes.
5. Add provenance data (source block) to trace nutrition back to its origin.
6. Add price entries for the relevant country/region/currency.
7. Run a dry-run before import.

## Documentation

- `docs/food_data_spec.md` — Canonical food data specification
- `docs/data_sources.md` — Source strategy and licensing analysis
- `docs/validation_rules.md` — Full validation rule set
- `docs/dataset_phasing.md` — Dataset phasing plan (200-300 foods)

## Running tests

`uv run python -m pytest -q`

`uv run ruff check app tests -q`
