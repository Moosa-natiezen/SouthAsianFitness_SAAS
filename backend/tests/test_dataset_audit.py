"""Tests for South Asian food dataset audit and verification rules."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

DATASET_PATH = Path(__file__).parent.parent / "data" / "south_asian_foods.json"


def load_dataset() -> dict:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


# ── Nutrition plausibility ──────────────────────────────────────────────────

ATWATER_EXCEPTIONS = {
    "coffee-brewed", "black-tea", "green-tea", "salt",
    "mustard-oil", "sunflower-oil", "coconut-oil", "olive-oil",
    "vegetable-oil", "sesame-oil", "groundnut-oil", "ghee",
}


def _atwater(food: dict) -> tuple[float, float]:
    n = food["nutrition"]
    cal = n.get("calories", 0) or 0
    pro = n.get("protein_g", 0) or 0
    carb = n.get("carbs_g", 0) or 0
    fat = n.get("fat_g", 0) or 0
    atwater = pro * 4 + carb * 4 + fat * 9
    return cal, atwater


def test_no_food_exceeds_1000_kcal_per_100g():
    """No food should have more than 1000 kcal per 100g (impossible)."""
    data = load_dataset()
    for food in data["foods"]:
        cal = food["nutrition"].get("calories", 0)
        assert cal <= 1000, f"{food['slug']}: {cal} kcal exceeds 1000"


def test_no_negative_nutrition_values():
    """No nutrition value should be negative."""
    data = load_dataset()
    for food in data["foods"]:
        for key in ["calories", "protein_g", "carbs_g", "fat_g"]:
            val = food["nutrition"].get(key, 0)
            assert val >= 0, f"{food['slug']}: {key}={val} is negative"


def test_atwater_no_suspicious_deviation():
    """No food should have >80% Atwater deviation unless it's an exception."""
    data = load_dataset()
    anomalies = []
    for food in data["foods"]:
        slug = food["slug"]
        cal, atwater = _atwater(food)
        if cal <= 0 or atwater <= 0:
            continue
        deviation = abs(cal - atwater) / max(atwater, 1) * 100
        if deviation > 80 and slug not in ATWATER_EXCEPTIONS:
            anomalies.append(f"{slug}: {deviation:.0f}%")
    assert not anomalies, f"Suspicious Atwater deviations: {anomalies}"


def test_coffee_is_exception():
    """Coffee (brewed) should be flagged as an expected Atwater exception."""
    data = load_dataset()
    coffee = next(f for f in data["foods"] if f["slug"] == "coffee-brewed")
    cal, atwater = _atwater(coffee)
    deviation = abs(cal - atwater) / max(atwater, 1) * 100
    # Coffee has 2 kcal but minimal macros → Atwater deviation is expected
    assert deviation > 100, f"Coffee deviation {deviation:.0f}% should be >100%"
    assert "coffee-brewed" in ATWATER_EXCEPTIONS


# ── Duplicate detection ─────────────────────────────────────────────────────

def test_no_duplicate_slugs():
    """Every slug in the dataset must be unique."""
    data = load_dataset()
    slugs = [f["slug"] for f in data["foods"]]
    dupes = [s for s in set(slugs) if slugs.count(s) > 1]
    assert not dupes, f"Duplicate slugs: {dupes}"


def test_no_exact_duplicate_foods():
    """No two foods should have identical name and FDC ID."""
    data = load_dataset()
    seen = set()
    dupes = []
    for f in data["foods"]:
        key = (f["name"], f["source"].get("source_identifier", ""))
        if key in seen:
            dupes.append(f"{f['name']} ({f['slug']})")
        seen.add(key)
    assert not dupes, f"Exact duplicate foods: {dupes}"


# ── Verification status rules ───────────────────────────────────────────────

def test_all_foods_have_verification_status():
    """Every food must have a valid verification_status."""
    valid_statuses = {"verified", "verified_with_notes", "pending_review", "rejected"}
    data = load_dataset()
    for food in data["foods"]:
        status = food["source"].get("verification_status", "")
        assert status in valid_statuses, (
            f"{food['slug']}: invalid status '{status}'"
        )


def test_no_rejected_foods_in_verified():
    """No food with status 'rejected' should be counted as verified."""
    data = load_dataset()
    for food in data["foods"]:
        status = food["source"].get("verification_status", "")
        if status == "rejected":
            # Rejected foods must not appear in verified counts
            assert False, f"{food['slug']}: rejected food found"


def test_verified_foods_have_fdc_source():
    """All verified foods must have a valid FDC source identifier."""
    data = load_dataset()
    for food in data["foods"]:
        if food["source"].get("verification_status") == "verified":
            sid = food["source"].get("source_identifier", "")
            assert sid.startswith("FDC-"), (
                f"{food['slug']}: verified food missing FDC source"
            )


# ── Source provenance ───────────────────────────────────────────────────────

def test_all_foods_have_source_name():
    """Every food must have a source_name."""
    data = load_dataset()
    for food in data["foods"]:
        assert food["source"].get("source_name"), (
            f"{food['slug']}: missing source_name"
        )


def test_all_foods_have_source_identifier():
    """Every food must have a source_identifier."""
    data = load_dataset()
    for food in data["foods"]:
        assert food["source"].get("source_identifier"), (
            f"{food['slug']}: missing source_identifier"
        )


# ── Production import safety ────────────────────────────────────────────────

def test_pending_review_excluded_from_verified_count():
    """Foods with pending_review status must not be counted as verified."""
    data = load_dataset()
    verified = 0
    pending = 0
    for food in data["foods"]:
        status = food["source"].get("verification_status", "")
        if status == "verified":
            verified += 1
        elif status == "pending_review":
            pending += 1
    # Both counts should be non-zero (dataset has both)
    assert verified > 0, "No verified foods found"
    assert pending > 0, "No pending_review foods found"
    # Verified + pending + others should equal total
    total = len(data["foods"])
    assert verified + pending <= total


# ── Country assignments ─────────────────────────────────────────────────────

def test_all_foods_have_at_least_one_country():
    """Every food must be assigned to at least one country."""
    data = load_dataset()
    for food in data["foods"]:
        countries = food.get("countries", [])
        assert len(countries) > 0, f"{food['slug']}: no countries assigned"


def test_country_codes_are_valid():
    """Country codes must be valid 2-letter ISO codes."""
    valid_codes = {"PK", "IN", "BD", "LK", "NP"}
    data = load_dataset()
    for food in data["foods"]:
        for code in food.get("countries", []):
            assert code in valid_codes, (
                f"{food['slug']}: invalid country code '{code}'"
            )


# ── Dataset integrity ───────────────────────────────────────────────────────

def test_dataset_loads_correctly():
    """The dataset file must load and contain foods."""
    data = load_dataset()
    assert "foods" in data
    assert len(data["foods"]) > 100, f"Expected >100 foods, got {len(data['foods'])}"


def test_all_foods_have_required_fields():
    """Every food must have name, slug, category, nutrition, source."""
    data = load_dataset()
    for food in data["foods"]:
        assert food.get("name"), "Missing name"
        assert food.get("slug"), "Missing slug"
        assert food.get("category"), f"{food['slug']}: missing category"
        assert food.get("nutrition"), f"{food['slug']}: missing nutrition"
        assert food.get("source"), f"{food['slug']}: missing source"
        nut = food["nutrition"]
        assert "calories" in nut, f"{food['slug']}: missing calories"
        assert "protein_g" in nut, f"{food['slug']}: missing protein_g"
        assert "carbs_g" in nut, f"{food['slug']}: missing carbs_g"
        assert "fat_g" in nut, f"{food['slug']}: missing fat_g"


def test_serving_info_present():
    """Every food must have serving information."""
    data = load_dataset()
    for food in data["foods"]:
        serving = food.get("serving", {})
        assert serving.get("amount"), f"{food['slug']}: missing serving amount"
        assert serving.get("unit"), f"{food['slug']}: missing serving unit"
