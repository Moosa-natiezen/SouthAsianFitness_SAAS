# Canonical Food Data Specification

This document defines the canonical format for every food record in the
Freebuff food database. It covers identity, geography, nutrition, serving,
ingredients, and provenance.

---

## 1. Identity

Every food must have a unique identity.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string (255) | Yes | Canonical display name in English |
| `slug` | string (150) | Yes | URL-safe unique identifier; normalized lowercase |
| `description` | text | No | Brief description of the food |
| `food_type` | enum | Yes | `ingredient` or `composite` |
| `category` | string (100) | Yes | Food category slug (auto-created if missing) |
| `alternate_names` | list[string] | No | Local language names, regional names (stored in `translations` JSON) |

### Slug Rules

- Lowercase, alphanumeric + hyphens only.
- Derived from name: `"Chicken Biryani"` → `"chicken-biryani"`.
- Must be globally unique across all imported datasets.
- Duplicate slugs within a single import batch are rejected.

### Food Type

- **`ingredient`**: A single unprocessed or minimally processed food
  (e.g., "basmati rice", "chicken breast", "onion").
- **`composite`**: A prepared dish made from multiple ingredients
  (e.g., "chicken biryani", "dal makhani", "fish curry").

---

## 2. Geography

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `countries` | list[ISO-3166-1 alpha-2] | Yes (≥1) | Country codes where this food is commonly consumed |
| `regions` | list[string] | No | Specific regions/states/provinces |

### Country Codes

Standard ISO 3166-1 alpha-2 codes:

| Country | Code |
|---------|------|
| Pakistan | PK |
| India | IN |
| Bangladesh | BD |
| Sri Lanka | LK |
| Nepal | NP |

A food must be associated with at least one country. A food commonly eaten
across South Asia should list all relevant countries.

---

## 3. Nutrition

All nutrition values are expressed **per the reference quantity** (typically
per 100g or per standard serving).

| Field | Type | Required | Unit | Constraints |
|-------|------|----------|------|-------------|
| `calories` | decimal(10,2) | Yes | kcal | ≥ 0 |
| `protein_g` | decimal(10,3) | Yes | grams | ≥ 0 |
| `carbs_g` | decimal(10,3) | Yes | grams | ≥ 0 |
| `fat_g` | decimal(10,3) | Yes | grams | ≥ 0 |
| `fiber_g` | decimal(10,3) | No | grams | ≥ 0 |
| `sugar_g` | decimal(10,3) | No | grams | ≥ 0 |
| `sodium_mg` | decimal(10,3) | No | mg | ≥ 0 |

### Additional Nutrients (future extensions)

Where reliably available from authoritative sources, these may be added:

- Calcium (mg), Iron (mg), Potassium (mg)
- Vitamin A (mcg RAE), Vitamin C (mg), Vitamin D (mcg)
- Cholesterol (mg)
- Saturated fat (g), Trans fat (g), Omega-3 (g)

Only add these when available from a trusted source. Do not guess or
interpolate missing micronutrients.

---

## 4. Serving

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | decimal(10,3) | Yes | Reference quantity for the nutrition values |
| `unit` | string (32) | Yes | Unit code (from the units table) |
| `grams_equivalent` | decimal(10,3) | No | Weight in grams when the unit is count/volume |

### Standard Serving Units

| Code | Name | Dimension | Grams Equivalent |
|------|------|-----------|------------------|
| `g` | gram | mass | 1 |
| `kg` | kilogram | mass | 1000 |
| `ml` | milliliter | volume | ~1 (water) |
| `l` | liter | volume | ~1000 (water) |
| `cup` | cup | volume | ~240 |
| `tbsp` | tablespoon | volume | ~15 |
| `tsp` | teaspoon | volume | ~5 |
| `pc` | piece | count | Varies |
| `serving` | serving | count | Varies (set `grams_equivalent`) |
| `roti` | roti | count | ~60 |

### Household Serving Conventions

South Asian households commonly use:

- **1 roti** ≈ 60g
- **1 bowl (katori)** ≈ 150–200g
- **1 plate (thali)** ≈ 300–400g
- **1 glass** ≈ 250ml
- **1 cup chai** ≈ 150ml

Always provide `grams_equivalent` for count-based units so nutrition can be
accurately calculated.

---

## 5. Ingredients

For composite foods only. Each ingredient links to another food record.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string (200) | Yes | Display name of the ingredient |
| `slug` | string (200) | No | Slug of the ingredient food record (auto-created if missing) |
| `quantity` | decimal(10,3) | Yes | Amount of this ingredient |
| `unit` | string (32) | Yes | Unit code |
| `notes` | string (255) | No | Preparation notes (e.g., "finely chopped", "marinated") |

### Ingredient Rules

- An ingredient must reference an existing food by slug, or a new ingredient
  food record is auto-created with zeroed nutrition.
- Ingredient quantities and units must be consistent with the parent food's
  reference quantity.
- Duplicate ingredient entries (same parent + same ingredient) are ignored.

---

## 6. Provenance

Every food record MUST be traceable to its data source.

### Per-Food Provenance Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `food_source_id` | UUID | No | FK to the `food_sources` table |
| `source_identifier` | string (255) | No | Source-specific ID (e.g., USDA FDC ID, IFCT code) |
| `source_version` | string (64) | No | Version of the source data used |
| `source_date` | datetime | No | Date of the source data |
| `imported_at` | datetime | No | When this record was imported |
| `verification_status` | enum | Yes | See below |

### Verification Status

| Value | Meaning |
|-------|---------|
| `unverified` | Data from community sources or internal estimates; not yet reviewed |
| `pending_review` | Imported from an authoritative source; awaiting human review |
| `verified` | Confirmed accurate by a human reviewer or cross-referencing |
| `conflict` | Conflicting data from multiple sources; requires resolution |
| `retracted` | Data has been retracted or is known to be incorrect |

### FoodSource Record

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string (150) | Yes | Source name (e.g., "USDA FoodData Central") |
| `version` | string (64) | Yes | Version identifier |
| `reference_url` | text | No | URL to the source |
| `license_category` | enum | Yes | See `FoodSourceLicense` enum |
| `attribution_text` | text | No | Required attribution text |
| `can_store_raw_data` | boolean | Yes | Whether we may store raw data from this source |
| `can_store_derived_values` | boolean | Yes | Whether we may store derived/normalized values |
| `description` | text | No | Description of the source |
| `source_date` | datetime | No | Date of the source data |
| `imported_at` | datetime | No | When this source was first imported |

---

## 7. Sample Record (JSON Import Format)

```json
{
  "name": "Chicken Biryani",
  "slug": "chicken-biryani",
  "description": "Aromatic rice dish with spiced chicken, popular across South Asia.",
  "food_type": "composite",
  "category": "prepared-meals",
  "countries": ["PK", "IN", "BD"],
  "regions": ["Punjab", "Hyderabad"],
  "nutrition": {
    "calories": 350,
    "protein_g": 22,
    "carbs_g": 40,
    "fat_g": 12,
    "fiber_g": 2,
    "sugar_g": 3,
    "sodium_mg": 580
  },
  "serving": {
    "amount": 1,
    "unit": "serving",
    "grams_equivalent": 300
  },
  "ingredients": [
    {"name": "basmati rice", "slug": "basmati-rice", "quantity": 150, "unit": "g"},
    {"name": "chicken", "slug": "chicken-breast", "quantity": 120, "unit": "g"},
    {"name": "onion", "slug": "onion", "quantity": 30, "unit": "g"},
    {"name": "yogurt", "slug": "plain-yogurt", "quantity": 20, "unit": "g"},
    {"name": "ghee", "slug": "ghee", "quantity": 10, "unit": "g"},
    {"name": "biryani masala", "slug": "biryani-masala", "quantity": 5, "unit": "g"}
  ],
  "source": {
    "source_name": "ICMR-NIN Indian Food Composition Tables",
    "source_identifier": "IFCT-2017-042",
    "source_version": "2017",
    "source_date": "2017-01-01T00:00:00+00:00",
    "verification_status": "pending_review",
    "notes": "Values adjusted for home preparation; original is restaurant-style"
  },
  "prices": [
    {
      "country": "PK",
      "region": "Punjab",
      "currency": "PKR",
      "amount": 350,
      "quantity": 1,
      "unit": "serving",
      "observed_at": "2026-08-01T00:00:00+00:00"
    }
  ]
}
```

---

## 8. Dataset-Level Source Metadata

A dataset file may include a `dataset_source` block that applies to all
foods in the file unless overridden by a per-record `source` block.

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
    "source_date": "2024-06-01T00:00:00+00:00",
    "description": "USDA nutrient data for base ingredients."
  },
  "foods": [ ... ]
}
```

### Source Resolution Priority

1. Per-record `source` block → creates/uses a specific `FoodSource`
2. Dataset-level `dataset_source` → creates/uses a shared `FoodSource`
3. No source specified → `food_source_id` is NULL, status is `unverified`
