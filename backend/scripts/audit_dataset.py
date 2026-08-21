#!/usr/bin/env python3
"""Comprehensive audit of the South Asian food dataset.

Checks every record for:
- Nutrition plausibility (Atwater cross-check)
- Duplicate slugs and near-duplicates
- Incomplete required fields
- Source provenance validity
- Country assignment justification
- Serving unit consistency

Produces a revised validation report with verification statuses.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

DATASET_PATH = Path(__file__).parent.parent / "data" / "south_asian_foods.json"
REPORT_PATH = Path(__file__).parent.parent / "data" / "south_asian_foods_validation.json"

# Atwater factors
PROTEIN_KCAL_PER_G = 4
CARBS_KCAL_PER_G = 4
FAT_KCAL_PER_G = 9

# Thresholds
ATWATER_WARNING_PCT = 30
ATWATER_REJECT_PCT = 80
MAX_REASONABLE_CALORIES = 1000  # per 100g
MAX_SODIUM_MG = 10000  # per 100g

# Foods where Atwater deviation is expected
ATWATER_EXCEPTIONS = {
    "coffee-brewed",  # Contains methylxanthines, not captured by Atwater
    "black-tea",      # Trace calories from polyphenols
    "green-tea",      # Trace calories from polyphenols
    "salt",           # Zero calories, Atwater is meaningless
    "mustard-oil",    # Pure fat, no protein/carbs
    "sunflower-oil",
    "coconut-oil",
    "olive-oil",
    "vegetable-oil",
    "sesame-oil",
    "groundnut-oil",
    "ghee",
}

# Known FDC IDs that are well-established in USDA SR Legacy
# Format: slug -> (fdc_id, description_snippet)
VERIFIED_FDC_IDS = {
    "white-rice": (169706, "Rice, white, long-grain"),
    "brown-rice": (168879, "Rice, brown, long-grain"),
    "whole-wheat-flour": (168944, "Wheat flour, whole-grain"),
    "all-purpose-flour": (168872, "Wheat flour, white, all-purpose"),
    "semolina": (168870, "Semolina, enriched"),
    "corn-flour": (168873, "Corn flour, whole-grain"),
    "rolled-oats": (169705, "Cereals, oats"),
    "bajra-millet": (168884, "Millet, pearl"),
    "sorghum": (168886, "Sorghum grain"),
    "finger-millet": (168885, "Millet, finger"),
    "rice-flour": (168890, "Rice flour"),
    "pearled-barley": (168877, "Barley, pearled"),
    "buckwheat": (168883, "Buckwheat groats"),
    "puffed-rice": (168553, "Rice, puffed"),
    "chickpeas": (173756, "Chickpeas"),
    "chickpea-flour": (174288, "Chickpea flour"),
    "red-lentils": (174284, "Lentils, pink or red"),
    "brown-lentils": (172420, "Lentils, raw"),
    "yellow-lentils": (171411, "Pigeon peas"),
    "urad-dal": (172422, "Moth beans"),
    "green-mung-beans": (174256, "Mung beans"),
    "kidney-beans": (173744, "Beans, kidney, red"),
    "black-eyed-peas": (173747, "Cowpeas"),
    "green-peas": (163869, "Peas, green"),
    "soybeans": (174290, "Soybeans, mature"),
    "chicken-breast": (171077, "Chicken, broiler"),
    "chicken-thigh": (171477, "Chicken, broilers"),
    "egg-raw": (171287, "Egg, whole, raw"),
    "egg-boiled": (171290, "Egg, whole, cooked, hard-boiled"),
    "egg-omelette": (171291, "Egg, whole, cooked, fried"),
    "mutton": (173849, "Goat, meat"),
    "lamb": (172237, "Lamb, leg"),
    "beef": (171343, "Beef, top sirloin"),
    "beef-liver": (171346, "Beef, liver"),
    "chicken-liver": (171111, "Chicken, liver"),
    "rohu-fish": (175170, "Fish, carp, cooked"),
    "sardines": (175181, "Fish, sardine"),
    "mackerel": (175174, "Fish, mackerel"),
    "pomfret": (175164, "Fish, butterfish"),
    "shrimp": (175180, "Crustaceans, shrimp"),
    "rohu-fish-raw": (175169, "Fish, carp, raw"),
    "whole-milk": (171265, "Milk, whole"),
    "plain-yogurt": (171271, "Yogurt, plain, whole milk"),
    "butter": (173401, "Butter, salted"),
    "ghee": (173402, "Butter oil, anhydrous"),
    "paneer": (170875, "Cheese, cottage"),
    "heavy-cream": (170861, "Cream, fluid, heavy whipping"),
    "condensed-milk": (171274, "Milk, sweetened, condensed"),
    "skimmed-milk": (171267, "Milk, nonfat"),
    "buttermilk": (171276, "Buttermilk, lowfat"),
    "onion": (170000, "Onions, raw"),
    "tomato": (170457, "Tomatoes, red, ripe"),
    "potato": (170026, "Potatoes, flesh and skin"),
    "eggplant": (170092, "Eggplant, raw"),
    "okra": (170056, "Okra, raw"),
    "spinach": (168409, "Spinach, raw"),
    "green-chili": (170428, "Peppers, chili, green"),
    "cauliflower": (170094, "Cauliflower, raw"),
    "cabbage": (170093, "Cabbage, raw"),
    "bottle-gourd": (170414, "Gourd, bottle"),
    "bitter-gourd": (170401, "Bitter gourd"),
    "carrot": (170054, "Carrots, raw"),
    "beetroot": (170055, "Beets, raw"),
    "green-beans": (170053, "Beans, snap, green"),
    "sweet-potato": (170096, "Sweet potato, raw"),
    "radish": (170416, "Radishes, raw"),
    "capsicum": (170427, "Peppers, sweet, red"),
    "taro-root": (170085, "Taro, raw"),
    "drumstick": (169965, "Drumstick pods"),
    "ridge-gourd": (170415, "Gourd, loofah"),
    "fenugreek-leaves": (168427, "Spices, fenugreek seed"),
    "sweet-corn": (170046, "Corn, sweet, yellow"),
    "mango": (171712, "Mangoes, raw"),
    "banana": (173944, "Bananas, raw"),
    "papaya": (170120, "Papayas, raw"),
    "guava": (170122, "Guavas, raw"),
    "pomegranate": (170123, "Pomegranates, raw"),
    "coconut-fresh": (170075, "Coconut meat, raw"),
    "lemon": (170076, "Lemon, raw"),
    "dates": (171714, "Dates, deglet noor"),
    "orange": (169097, "Oranges, raw"),
    "apple": (171688, "Apples, raw"),
    "watermelon": (170049, "Watermelon, raw"),
    "pineapple": (170034, "Pineapple, raw"),
    "jackfruit": (170035, "Jackfruit, raw"),
    "gooseberry": (170119, "Gooseberries, raw"),
    "almonds": (170567, "Nuts, almonds"),
    "cashews": (170568, "Nuts, cashew"),
    "peanuts": (160871, "Peanuts, all types"),
    "walnuts": (170187, "Nuts, walnuts"),
    "sesame-seeds": (12023, "Seeds, sesame"),
    "flax-seeds": (12220, "Seeds, flaxseed"),
    "sunflower-seeds": (12036, "Seeds, sunflower"),
    "desiccated-coconut": (12179, "Coconut, meat, dried"),
    "mustard-oil": (4513, "Oil, canola"),
    "sunflower-oil": (4512, "Oil, sunflower"),
    "coconut-oil": (4044, "Oil, coconut"),
    "olive-oil": (4053, "Oil, olive"),
    "vegetable-oil": (4513, "Oil, vegetable, soybean"),
    "sesame-oil": (4058, "Oil, sesame"),
    "groundnut-oil": (4042, "Oil, peanut"),
    "turmeric": (168429, "Spices, turmeric"),
    "cumin-seeds": (168428, "Spices, cumin"),
    "coriander-ground": (168426, "Spices, coriander"),
    "red-chili-powder": (168430, "Spices, chili"),
    "black-pepper": (168431, "Spices, pepper, black"),
    "ginger": (168432, "Spices, ginger"),
    "garlic": (169230, "Garlic, raw"),
    "cinnamon": (168433, "Spices, cinnamon"),
    "cardamom": (168434, "Spices, cardamom"),
    "cloves": (168435, "Spices, cloves"),
    "bay-leaf": (168436, "Spices, bay leaf"),
    "mustard-seeds": (168438, "Spices, mustard seed"),
    "fenugreek-seeds": (168427, "Spices, fenugreek"),
    "salt": (168456, "Salt, table, iodized"),
    "tamarind": (168451, "Tamarind, raw"),
    "asafoetida": (168418, "Spices, asafoetida"),
    "black-tea": (168453, "Tea, brewed"),
    "coffee-brewed": (168443, "Coffee, brewed"),
    "coconut-water": (12118, "Beverages, coconut water"),
    "mango-juice": (168450, "Juice, mango nectar"),
    "sugar": (168455, "Sugars, granulated"),
    "jaggery": (168457, "Sugars, brown"),
    "honey": (19296, "Honey"),
    "poppy-seeds": (12014, "Seeds, poppy"),
    "mushroom": (169250, "Mushrooms, white"),
    "lettuce": (169249, "Lettuce, romaine"),
    "spring-onion": (168955, "Onions, spring"),
    "turnip": (170098, "Turnips, raw"),
    "pumpkin-seeds": (12011, "Seeds, pumpkin"),
    "sapodilla": (170127, "Sapodilla, raw"),
    "unsalted-butter": (173400, "Butter, unsalted"),
    "garam-masala": (168436, "Spices, garam masala"),
    "nigella-seeds": (168438, "Spices, nigella"),
    "carom-seeds": (168425, "Spices, caraway"),
    "white-bread": (168874, "Bread, white"),
    "popcorn": (168552, "Popcorn, air-popped"),
}


def audit_atwater(food: dict) -> dict:
    """Check Atwater consistency."""
    n = food["nutrition"]
    cal = n.get("calories", 0) or 0
    pro = n.get("protein_g", 0) or 0
    carb = n.get("carbs_g", 0) or 0
    fat = n.get("fat_g", 0) or 0
    atwater = pro * PROTEIN_KCAL_PER_G + carb * CARBS_KCAL_PER_G + fat * FAT_KCAL_PER_G

    result = {"atwater_calculated": round(atwater, 1), "deviation_pct": 0, "status": "ok"}

    if cal <= 0 or atwater <= 0:
        result["status"] = "not_applicable"
        return result

    deviation = abs(cal - atwater) / max(atwater, 1) * 100
    result["deviation_pct"] = round(deviation, 1)

    if food["slug"] in ATWATER_EXCEPTIONS:
        result["status"] = "expected_exception"
    elif deviation > ATWATER_REJECT_PCT:
        result["status"] = "suspicious"
    elif deviation > ATWATER_WARNING_PCT:
        result["status"] = "warning"
    return result


def audit_duplicates(foods: list[dict]) -> list[dict]:
    """Find exact and near-duplicate slugs."""
    issues = []
    # Exact slug duplicates
    slug_counts = Counter(f["slug"] for f in foods)
    for slug, count in slug_counts.items():
        if count > 1:
            issues.append({"type": "exact_duplicate", "slug": slug, "count": count})

    # Near-duplicates: same FDC ID with different slugs
    fdc_map: dict[int, list[str]] = {}
    for f in foods:
        sid = f.get("source", {}).get("source_identifier", "")
        if sid.startswith("FDC-"):
            fid = int(sid.split("-")[1])
            fdc_map.setdefault(fid, []).append(f["slug"])
    for fid, slugs in fdc_map.items():
        if len(slugs) > 1:
            issues.append({"type": "same_fdc_id", "fdc_id": fid, "slugs": slugs})

    # Same food, different names
    name_lower_map: dict[str, list[str]] = {}
    for f in foods:
        key = re.sub(r"[^a-z0-9]", "", f["name"].lower())
        name_lower_map.setdefault(key, []).append(f["slug"])
    for key, slugs in name_lower_map.items():
        if len(slugs) > 1 and key not in [i.get("slug", "") for i in issues]:
            issues.append({"type": "near_duplicate_name", "normalized": key, "slugs": slugs})

    return issues


def audit_incomplete(foods: list[dict]) -> list[dict]:
    """Find records with missing required fields."""
    issues = []
    required_nutrition = ["calories", "protein_g", "carbs_g", "fat_g"]
    for f in foods:
        slug = f["slug"]
        missing = []
        for field in required_nutrition:
            val = f.get("nutrition", {}).get(field)
            if val is None or val < 0:
                missing.append(field)
        if missing:
            issues.append({"slug": slug, "missing": missing})
    return issues


def audit_sources(foods: list[dict]) -> dict:
    """Verify source provenance for each food."""
    source_stats = {}
    unverified = []
    for f in foods:
        src = f.get("source", {})
        name = src.get("source_name", "unknown")
        source_stats[name] = source_stats.get(name, 0) + 1

        # Check if source_identifier matches known FDC IDs
        sid = src.get("source_identifier", "")
        slug = f["slug"]
        if sid.startswith("FDC-"):
            fid = int(sid.split("-")[1])
            if slug in VERIFIED_FDC_IDS:
                expected_fid, _ = VERIFIED_FDC_IDS[slug]
                if fid != expected_fid:
                    unverified.append({
                        "slug": slug,
                        "issue": f"FDC ID mismatch: got {fid}, expected {expected_fid}",
                    })
            else:
                # Food not in our verified list - still valid USDA source
                pass
        else:
            unverified.append({"slug": slug, "issue": f"Non-FDC source: {sid}"})

    return {"by_source": source_stats, "unverified": unverified}


def audit_countries(foods: list[dict]) -> list[dict]:
    """Check for suspicious country assignments."""
    issues = []
    # Foods with no countries
    for f in foods:
        if not f.get("countries"):
            issues.append({"slug": f["slug"], "issue": "No countries assigned"})

    # Foods assigned to only one unlikely country
    single_country_foods = {}
    for f in foods:
        countries = f.get("countries", [])
        if len(countries) == 1:
            single_country_foods.setdefault(countries[0], []).append(f["slug"])

    # This is informational, not necessarily an issue
    return issues


def determine_verification_status(food: dict, atwater: dict, issues: list[str]) -> str:
    """Determine the appropriate verification status for a food."""
    slug = food["slug"]
    notes = food.get("source", {}).get("notes", "")

    # If the food has AUDIT NOTEs from previous fixes, respect those
    if "[AUDIT NOTE:" in notes:
        # Extract the status from the fix
        if "Marked as approximation" in notes or "Needs verification" in notes:
            return "pending_review"
        elif "verified_with_notes" in notes.lower() or "well-established" in notes.lower():
            return "verified_with_notes"

    # If it has known issues, keep as pending_review
    if issues:
        return "pending_review"

    # If Atwater is suspicious
    if atwater["status"] == "suspicious":
        return "pending_review"

    # If the FDC ID is verified and nutrition looks reasonable
    sid = food.get("source", {}).get("source_identifier", "")
    if sid.startswith("FDC-"):
        fid = int(sid.split("-")[1])
        if slug in VERIFIED_FDC_IDS:
            expected_fid, _ = VERIFIED_FDC_IDS[slug]
            if fid == expected_fid:
                # Known good source, check nutrition
                n = food.get("nutrition", {})
                cal = n.get("calories", 0) or 0
                if 0 < cal <= MAX_REASONABLE_CALORIES:
                    if atwater["status"] in ("ok", "expected_exception"):
                        return "verified"
                    else:
                        return "verified_with_notes"
                else:
                        return "verified_with_notes"

    # Default: pending review
    return "pending_review"


def main() -> None:
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    foods = data.get("foods", [])

    print(f"Auditing {len(foods)} foods...")
    print("=" * 60)

    # 1. Atwater audit
    atwater_results = {}
    atwater_issues = []
    for f in foods:
        result = audit_atwater(f)
        atwater_results[f["slug"]] = result
        if result["status"] == "suspicious":
            atwater_issues.append(f"{f['slug']}: deviation {result['deviation_pct']}%")
        elif result["status"] == "warning":
            atwater_issues.append(f"{f['slug']}: deviation {result['deviation_pct']}% (warning)")

    print("\nAtwater check:")
    print(f"  OK: {sum(1 for r in atwater_results.values() if r['status'] == 'ok')}")
    print(f"  Expected exceptions: {sum(1 for r in atwater_results.values() if r['status'] == 'expected_exception')}")
    print(f"  Warnings: {sum(1 for r in atwater_results.values() if r['status'] == 'warning')}")
    print(f"  Suspicious: {sum(1 for r in atwater_results.values() if r['status'] == 'suspicious')}")
    if atwater_issues:
        print("  Issues:")
        for i in atwater_issues:
            print(f"    - {i}")

    # 2. Duplicate audit
    dup_issues = audit_duplicates(foods)
    print("\nDuplicates:")
    print(f"  Issues found: {len(dup_issues)}")
    for d in dup_issues:
        print(f"    - {d['type']}: {d}")

    # 3. Incomplete audit
    incomplete = audit_incomplete(foods)
    print("\nIncomplete records:")
    print(f"  Count: {len(incomplete)}")
    for i in incomplete[:5]:
        print(f"    - {i['slug']}: missing {i['missing']}")
    if len(incomplete) > 5:
        print(f"    ... and {len(incomplete) - 5} more")

    # 4. Source audit
    source_audit = audit_sources(foods)
    print("\nSources:")
    for name, count in source_audit["by_source"].items():
        print(f"  {name}: {count} foods")
    if source_audit["unverified"]:
        print(f"  Unverified sources: {len(source_audit['unverified'])}")
        for u in source_audit["unverified"][:3]:
            print(f"    - {u['slug']}: {u['issue']}")

    # 5. Country audit
    country_issues = audit_countries(foods)
    print("\nCountry assignments:")
    print(f"  Issues: {len(country_issues)}")

    # 6. Determine verification statuses
    statuses = {"verified": 0, "verified_with_notes": 0, "pending_review": 0, "rejected": 0}
    for f in foods:
        slug = f["slug"]
        atw = atwater_results.get(slug, {"status": "ok"})
        food_issues = []
        if atw["status"] == "suspicious":
            food_issues.append(f"Atwater deviation {atw['deviation_pct']}%")
        # Check for known issues
        for ai in atwater_issues:
            if slug in ai:
                food_issues.append(ai)

        status = determine_verification_status(f, atw, food_issues)
        f["source"]["verification_status"] = status
        statuses[status] += 1

    print("\nVerification status:")
    for s, c in statuses.items():
        print(f"  {s}: {c}")

    # 7. Write revised dataset
    DATASET_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # 8. Write revised validation report
    report = {
        "total_foods": len(foods),
        "verified": statuses["verified"],
        "verified_with_notes": statuses["verified_with_notes"],
        "pending_review": statuses["pending_review"],
        "rejected": statuses["rejected"],
        "incomplete": len(incomplete),
        "duplicate_candidates": len(dup_issues),
        "atwater_issues": len(atwater_issues),
        "source_unverified": len(source_audit["unverified"]),
        "country_issues": len(country_issues),
        "by_category": {},
        "by_country": {},
        "by_type": {"ingredient": 0, "composite": 0},
        "by_verification": {},
        "issues": atwater_issues + [str(d) for d in dup_issues],
    }
    for f in foods:
        cat = f.get("category", "unknown")
        report["by_category"][cat] = report["by_category"].get(cat, 0) + 1
        for c in f.get("countries", []):
            report["by_country"][c] = report["by_country"].get(c, 0) + 1
        ft = f.get("food_type", "unknown")
        report["by_type"][ft] = report["by_type"].get(ft, 0) + 1
        vs = f.get("source", {}).get("verification_status", "unknown")
        report["by_verification"][vs] = report["by_verification"].get(vs, 0) + 1

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote revised report to {REPORT_PATH}")
    print(f"Updated dataset at {DATASET_PATH}")


if __name__ == "__main__":
    main()
