# Food Data Source Strategy

This document evaluates potential authoritative sources for South Asian food
nutrition data, their licensing constraints, and how they fit into our
provenance architecture.

## Source Hierarchy

The recommended source hierarchy for importing food data, ordered by
trustworthiness and licensing compatibility:

| Priority | Source | Coverage | License | Recommendation |
|----------|--------|----------|---------|----------------|
| 1 | USDA FoodData Central | Global staples, grains, legumes, dairy, oils | Public domain (CC0) | Primary source for base ingredients |
| 2 | ICMR-NIN Indian Food Composition Tables (IFCT) | Indian foods, traditional dishes, regional staples | Government publication; check latest terms | Primary source for Indian-specific foods |
| 3 | Sri Lanka USDA-equivalent / Food Composition Tables | Sri Lankan staples | Government publication; check terms | Secondary for Sri Lankan foods |
| 4 | Bangladesh Food Composition Tables (BNIN/IFST) | Bangladeshi staples | Government publication; check terms | Secondary for Bangladeshi foods |
| 5 | Nepal Food Composition Tables | Nepali staples | Government publication; check terms | Secondary for Nepali foods |
| 6 | Pakistan Agricultural Research Council (PARC) tables | Pakistani staples | Government publication; check terms | Secondary for Pakistani foods |
| 7 | Peer-reviewed literature / journal articles | Specific dishes, regional variants | Usually CC-BY or requires permission | Supplementary; use for derived values only |
| 8 | Community-verified / internal estimates | Custom dishes, household recipes | Internal | Mark as unverified; never primary source |

---

## Detailed Source Analysis

### 1. USDA FoodData Central

- **URL**: https://fdc.nal.usda.gov/
- **What data we can use**: Nutrient profiles for ~300,000+ foods including grains,
  legumes, dairy, oils, fruits, vegetables, spices, and many South Asian ingredients
  (e.g., basmati rice, chickpeas, lentils, ghee, yogurt).
- **Licensing**: **Public domain (CC0)**. The USDA explicitly places FDC data in the
  public domain. No attribution is legally required, though attribution is good practice.
- **Attribution required**: No (but recommended).
- **Can store raw data**: Yes. We may download and store raw nutrient data.
- **Can store derived/normalized values**: Yes.
- **Limitations**:
  - Limited coverage of *prepared* South Asian dishes (e.g., biryani, dal fry,
    chicken tikka).
  - Nutrient values may reflect US-market preparations, not home-cooked South
    Asian versions.
  - Serving sizes and reference quantities may need normalization to South Asian
    household measures.
  - Does not include pricing data.

### 2. ICMR-NIN Indian Food Composition Tables (IFCT 2017)

- **URL**: Published by ICMR-National Institute of Nutrition, Hyderabad.
- **What data we can use**: Comprehensive nutrient data for 528 Indian foods
  covering cereals, pulses, vegetables, fruits, spices, milk products, fish,
  meat, and prepared dishes.
- **Licensing**: Government of India publication. The 2017 edition is widely
  used in academic and commercial contexts in India, but terms for electronic
  redistribution should be verified with ICMR-NIN before commercial use.
  - **Action required**: Contact ICMR-NIN or review the publication's license
    terms before importing data for commercial electronic redistribution.
- **Attribution required**: Likely yes for any reproductions. Must cite:
  "Indian Food Composition Tables 2017, National Institute of Nutrition, ICMR."
- **Can store raw data**: Depends on license terms (pending verification).
- **Can store derived/normalized values**: More permissive than raw data.
  Derived values (e.g., per-100g calculations from stated portions) are
  generally safe to store.
- **Limitations**:
  - Limited to 528 foods (not comprehensive for all South Asian cuisines).
  - Values reflect 2017 analytical methods.
  - Does not include Bangladeshi, Pakistani, Sri Lankan, or Nepali-specific foods.
  - Regional variations within India not well captured.

### 3. Sri Lanka Food Composition Tables

- **Source**: Published by the University of Colombo / Ministry of Health.
- **What data we can use**: Nutrient data for Sri Lankan staples including
  rice varieties, coconut-based preparations, and tropical fruits.
- **Licensing**: Government publication. Terms for commercial electronic use
  should be verified.
  - **Action required**: Contact the publisher for license terms.
- **Attribution required**: Likely yes.
- **Can store raw data**: Pending license verification.
- **Can store derived/normalized values**: Likely more permissive.
- **Limitations**:
  - Smaller database than IFCT or USDA.
  - Focuses on Sri Lankan food items specifically.

### 4. Bangladesh Food Composition Tables

- **Source**: Institute of Food Science and Technology (IFST), Bangladesh.
- **What data we can use**: Nutrient data for Bangladeshi staples including
  river fish, rice varieties, and traditional preparations.
- **Licensing**: Government publication. Terms should be verified.
  - **Action required**: Contact IFST Bangladesh for license terms.
- **Attribution required**: Likely yes.
- **Can store raw data**: Pending verification.
- **Can store derived/normalized values**: Likely more permissive.
- **Limitations**:
  - Limited availability in digital format.
  - May require manual digitization from print sources.

### 5. Nepal Food Composition Tables

- **Source**: Published by the Nepal National Food and Nutrition Commission
  or similar government body.
- **What data we can use**: Nutrient data for Nepali staples including dal
  bhat components, mountain region foods, and fermented foods.
- **Licensing**: Government publication. Terms should be verified.
  - **Action required**: Contact the publishing authority.
- **Attribution required**: Likely yes.
- **Can store raw data**: Pending verification.
- **Can store derived/normalized values**: Likely more permissive.
- **Limitations**:
  - Very limited digital availability.
  - Smallest coverage among the sources considered.

### 6. Pakistan Agricultural Research Council (PARC)

- **Source**: PARC and provincial agricultural research institutes.
- **What data we can use**: Nutrient data for Pakistani staples including
  wheat varieties, legumes, dairy products, and meat.
- **Licensing**: Government publication. Terms should be verified.
  - **Action required**: Contact PARC for license terms.
- **Attribution required**: Likely yes.
- **Can store raw data**: Pending verification.
- **Can store derived/normalized values**: Likely more permissive.
- **Limitations**:
  - Limited digital availability.
  - May overlap significantly with USDA data for common ingredients.

### 7. Peer-Reviewed Literature

- **What data we can use**: Specific analytical studies on individual foods
  or dishes (e.g., nutrient content of specific biryani recipes, regional
  dhal preparations).
- **Licensing**: Typically CC-BY or requires publisher permission. Each
  article must be checked individually.
- **Attribution required**: Always. Full citation required.
- **Can store raw data**: Only with explicit permission from the publisher.
- **Can store derived/normalized values**: Generally yes under CC-BY.
- **Limitations**:
  - Fragmented, inconsistent methodologies across studies.
  - Small sample sizes.
  - Not systematic; cannot serve as a primary dataset.

### 8. Community-Verified / Internal Estimates

- **What data we can use**: Household recipes, family preparations, and
  region-specific variants not covered by authoritative sources.
- **Licensing**: Internal; no external licensing constraints.
- **Attribution required**: No.
- **Can store raw data**: Yes.
- **Can store derived/normalized values**: Yes.
- **Limitations**:
  - Must be clearly marked as `unverified` in the verification_status field.
  - Should never be the sole source for a food record.
  - High variability in preparation methods.

---

## Import Decision Rules

1. **Never silently overwrite** food data from a higher-priority source with
   data from a lower-priority source.
2. **Always record provenance**: Every food record MUST have a linked
   `FoodSource` or explicit provenance fields.
3. **License compliance**: Do not import raw data from sources with
   `proprietary_no_redist` licensing. Use only derived/normalized values
   for such sources, and only after legal review.
4. **Version tracking**: Each import must record the source version/date
   so we can re-import when updated data is released.
5. **Verification cascade**: Foods imported from authoritative sources
   (USDA, ICMR-NIN) start as `pending_review`. Foods from community
   sources start as `unverified`.

## Source Migration Path

```
Phase 1: USDA FoodData Central (public domain, immediate use)
  → Base ingredients: grains, legumes, dairy, oils, fruits, vegetables

Phase 2: ICMR-NIN IFCT (pending license verification)
  → Indian-specific foods, traditional dishes, spices

Phase 3: Country-specific tables (pending license verification per country)
  → Pakistan, Bangladesh, Sri Lanka, Nepal specifics

Phase 4: Peer-reviewed literature + internal estimates
  → Regional variants, prepared dishes, household recipes
```
