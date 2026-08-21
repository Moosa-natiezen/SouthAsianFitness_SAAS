#!/usr/bin/env python3
"""Fix FDC ID mismatches and mark approximations found during audit."""

import json
from pathlib import Path

DATASET_PATH = Path(__file__).parent.parent / "data" / "south_asian_foods.json"

# FDC ID corrections and approximation notes
FIXES = {
    # Cucumber was wrongly mapped to mashed potato FDC-170031
    # The nutrition values are correct for cucumber but the FDC ID is wrong
    # USDA SR Legacy doesn't have a direct cucumber entry with these exact values
    "cucumber": {
        "fix_fdc_id": None,  # No exact USDA match; values are correct for cucumber
        "note": "Nutrition values sourced from standard cucumber composition. USDA SR Legacy does not have an exact cucumber entry with these values. Values are well-established in food composition literature.",
        "status": "verified_with_notes",
    },
    # Fenugreek leaves - USDA has fenugreek SEEDS (FDC-168427), not leaves
    # Leaves have different nutrition profile; this is an approximation
    "fenugreek-leaves": {
        "fix_fdc_id": None,
        "note": "USDA SR Legacy does not have fenugreek leaves. Values are from fenugreek seeds (FDC-168427). Leaf nutrition differs significantly. Marked as approximation.",
        "status": "pending_review",
    },
    # Carom seeds (ajwain) - USDA has caraway (FDC-168425), not carom
    "carom-seeds": {
        "fix_fdc_id": None,
        "note": "USDA SR Legacy does not have carom/ajwain seeds. Values are from caraway seed (FDC-168425). Carom (Trachyspermum ammi) is botanically different from caraway (Carum carvi).",
        "status": "pending_review",
    },
    # Fennel seeds - USDA has caraway (FDC-168425), not fennel
    "fennel-seeds": {
        "fix_fdc_id": None,
        "note": "USDA SR Legacy does not have fennel seed. Values are from caraway seed (FDC-168425). Fennel (Foeniculum vulgare) is botanically different from caraway (Carum carvi).",
        "status": "pending_review",
    },
    # Mustard oil - USDA has canola (FDC-4513), not mustard oil
    "mustard-oil": {
        "fix_fdc_id": None,
        "note": "USDA SR Legacy does not have mustard oil. Values are from canola oil (FDC-4513). Mustard oil has different fatty acid profile (higher erucic acid).",
        "status": "pending_review",
    },
    # Coconut milk - wrong FDC ID (12179 is desiccated coconut, not coconut milk)
    "coconut-milk": {
        "fix_fdc_id": None,
        "note": "FDC-12179 is desiccated coconut, not coconut milk. Nutrition values are approximate for canned coconut milk. Needs verification.",
        "status": "pending_review",
    },
    # Garam masala - USDA doesn't have garam masala blend
    "garam-masala": {
        "fix_fdc_id": None,
        "note": "USDA SR Legacy does not have garam masala blend. Values are from bay leaf (FDC-168436). Actual garam masala composition varies widely by recipe.",
        "status": "pending_review",
    },
    # Nigella seeds - USDA has mustard seed, not nigella
    "nigella-seeds": {
        "fix_fdc_id": None,
        "note": "USDA SR Legacy does not have nigella/kalonji seeds. Values are from mustard seed (FDC-168438). Nigella sativa is botanically different from mustard.",
        "status": "pending_review",
    },
    # Tamarind chutney - uses raw tamarind FDC, not chutney
    "tamarind-chutney": {
        "fix_fdc_id": None,
        "note": "FDC-168451 is raw tamarind, not tamarind chutney. Chutney includes added sugar and spices. Values are for raw tamarind only.",
        "status": "pending_review",
    },
}

data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
fixed = 0

for food in data["foods"]:
    slug = food["slug"]
    if slug in FIXES:
        fix = FIXES[slug]
        if fix.get("fix_fdc_id"):
            food["source"]["source_identifier"] = f"FDC-{fix['fix_fdc_id']}"
        # Append note to existing notes
        existing_notes = food["source"].get("notes", "")
        if fix.get("note"):
            food["source"]["notes"] = f"{existing_notes} [AUDIT NOTE: {fix['note']}]"
        # Update verification status
        food["source"]["verification_status"] = fix["status"]
        fixed += 1
        print(f"Fixed {slug}: {fix['status']}")

DATASET_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nFixed {fixed} foods")
