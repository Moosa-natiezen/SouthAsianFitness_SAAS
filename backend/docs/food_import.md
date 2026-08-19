# Food import / seeding guide

This project uses a JSON dataset as the canonical import format because it preserves nested food metadata, ingredient relationships, prices, and serving information without forcing a lossy flattening step.

## Canonical schema

```json
{
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

## Adding new foods

1. Add a record to the JSON file.
2. Use a stable slug.
3. Include nutrition and serving metadata.
4. Add ingredient relationships for composite dishes.
5. Add price entries for the relevant country/region/currency.
6. Run a dry-run before import.

## Running tests

`uv run python -m pytest -q`

`uv run ruff check app tests -q`
