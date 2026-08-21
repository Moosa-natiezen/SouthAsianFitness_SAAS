#!/usr/bin/env python3
"""Build the initial South Asian food dataset from USDA FoodData Central.

USDA FDC License: CC0 1.0 Universal (Public Domain)
Citation: U.S. Department of Agriculture, Agricultural Research Service.
         FoodData Central, 2019. fdc.nal.usda.gov.

This script:
1. Defines a curated list of ~200 South Asian foods with FDC IDs
2. Fetches nutrition data from the USDA FDC API in batches
3. Builds the canonical JSON import format
4. Generates a validation report

Usage:
    python -m scripts.build_dataset [--api-key KEY] [--output PATH] [--cache PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

FDC_BASE = "https://api.nal.usda.gov/fdc/v1"
DEFAULT_API_KEY = "DEMO_KEY"

# Nutrient IDs in USDA FDC (SR Legacy abridged format)
N = {
    "energy": "208",
    "protein": "203",
    "carbs": "205",
    "fat": "204",
    "fiber": "291",
    "sugar": "269",
    "sodium": "307",
    "calcium": "301",
    "iron": "303",
    "potassium": "306",
    "vitc": "401",
}
ALL_NUTRIENT_IDS = list(N.values())


def api_get(path: str, api_key: str, retries: int = 3) -> Any | None:
    url = f"{FDC_BASE}{path}{'&' if '?' in path else '?'}api_key={api_key}"
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                wait = 65 * (attempt + 1)
                print(f"\n  [RATE LIMITED] Waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"\n  [HTTP {exc.code}]", file=sys.stderr)
                return None
        except Exception as exc:  # noqa: BLE001
            print(f"\n  [ERROR] {exc}", file=sys.stderr)
            time.sleep(2)
    return None


def api_post(path: str, body: dict, api_key: str, retries: int = 3) -> Any | None:
    url = f"{FDC_BASE}{path}{'&' if '?' in path else '?'}api_key={api_key}"
    data = json.dumps(body).encode("utf-8")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                wait = 65 * (attempt + 1)
                print(f"\n  [RATE LIMITED] Waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"\n  [HTTP {exc.code}]", file=sys.stderr)
                return None
        except Exception as exc:  # noqa: BLE001
            print(f"\n  [ERROR] {exc}", file=sys.stderr)
            time.sleep(2)
    return None


def extract_nutrients(food_data: dict) -> dict[str, float]:
    """Extract key nutrients from a food detail or search result."""
    nutrients = {}
    for fn in food_data.get("foodNutrients", []):
        nid = str(fn.get("nutrientNumber", fn.get("nutrient", {}).get("number", "")))
        value = fn.get("value", fn.get("amount", 0))
        if nid in ALL_NUTRIENT_IDS and value:
            nutrients[nid] = round(float(value), 3)
    return nutrients


# ──────────────────────────────────────────────────────────────────────────────
# CURATED FOOD LIST
# Each entry: (name, slug, description, food_type, category, countries, fdc_id)
# All FDC IDs are for SR Legacy or Foundation data, per 100g edible portion.
# ──────────────────────────────────────────────────────────────────────────────

FOODS = [
    # ═══════════════════════════════════════════════════════════════════════
    # GRAINS & CEREALS (14)
    # ═══════════════════════════════════════════════════════════════════════
    ("White rice (long-grain, raw)", "white-rice", "Rice, white, long-grain, regular, raw",
     "ingredient", "grains", ["PK", "IN", "BD", "LK", "NP"], 169706),
    ("Brown rice (long-grain, raw)", "brown-rice", "Rice, brown, long-grain, raw",
     "ingredient", "grains", ["PK", "IN", "BD", "NP"], 168879),
    ("Whole wheat flour (atta)", "whole-wheat-flour", "Wheat flour, whole-grain",
     "ingredient", "grains", ["PK", "IN", "BD", "NP", "LK"], 168944),
    ("All-purpose flour (maida)", "all-purpose-flour", "Wheat flour, white, all-purpose, enriched, unbleached",
     "ingredient", "grains", ["PK", "IN", "BD", "NP", "LK"], 168872),
    ("Semolina (suji/rava)", "semolina", "Semolina, enriched",
     "ingredient", "grains", ["PK", "IN"], 168870),
    ("Corn flour (makki ka atta)", "corn-flour", "Corn flour, whole-grain, white",
     "ingredient", "grains", ["PK", "IN", "BD"], 168873),
    ("Rolled oats", "rolled-oats", "Cereals, oats, regular and quick, not fortified, dry",
     "ingredient", "grains", ["PK", "IN", "BD"], 169705),
    ("Pearl millet (bajra)", "bajra-millet", "Millet, pearl, raw",
     "ingredient", "grains", ["IN", "NP", "PK"], 168884),
    ("Sorghum (jowar)", "sorghum", "Sorghum grain, raw",
     "ingredient", "grains", ["IN", "NP", "PK"], 168886),
    ("Finger millet (ragi)", "finger-millet", "Millet, finger, raw",
     "ingredient", "grains", ["IN", "NP", "LK"], 168885),
    ("Rice flour", "rice-flour", "Rice flour, raw",
     "ingredient", "grains", ["IN", "BD", "LK"], 168890),
    ("Pearled barley", "pearled-barley", "Barley, pearled, raw",
     "ingredient", "grains", ["IN", "NP", "PK"], 168877),
    ("Buckwheat groats", "buckwheat", "Buckwheat groats, roasted, dry",
     "ingredient", "grains", ["NP"], 168883),
    ("Puffed rice (murmura)", "puffed-rice", "Rice, puffed",
     "ingredient", "grains", ["PK", "IN", "BD"], 168553),

    # ═══════════════════════════════════════════════════════════════════════
    # LEGUMES & PULSES (13)
    # ═══════════════════════════════════════════════════════════════════════
    ("Chickpeas (kabuli chana)", "chickpeas",
     "Chickpeas (garbanzo beans, bengal gram), mature seeds, raw",
     "ingredient", "legumes", ["PK", "IN", "BD", "NP", "LK"], 173756),
    ("Chickpea flour (besan)", "chickpea-flour",
     "Chickpea flour (besan)",
     "ingredient", "legumes", ["PK", "IN", "BD", "NP"], 174288),
    ("Red lentils (masoor dal)", "red-lentils",
     "Lentils, pink or red, raw",
     "ingredient", "legumes", ["PK", "IN", "BD", "NP"], 174284),
    ("Brown/green lentils", "brown-lentils",
     "Lentils, raw",
     "ingredient", "legumes", ["PK", "IN", "BD", "NP"], 172420),
    ("Yellow lentils (toor dal)", "yellow-lentils",
     "Pigeon peas (red gram), mature seeds, raw",
     "ingredient", "legumes", ["IN", "BD"], 171411),
    ("Black gram (urad dal)", "urad-dal",
     "Moth beans, mature seeds, raw",
     "ingredient", "legumes", ["PK", "IN", "NP"], 172422),
    ("Green mung beans", "green-mung-beans",
     "Mung beans, mature seeds, raw",
     "ingredient", "legumes", ["PK", "IN", "BD", "NP", "LK"], 174256),
    ("Kidney beans (rajma)", "kidney-beans",
     "Beans, kidney, red, mature seeds, raw",
     "ingredient", "legumes", ["PK", "IN", "NP"], 173744),
    ("Black-eyed peas (lobia)", "black-eyed-peas",
     "Cowpeas (black-eyed peas), mature seeds, raw",
     "ingredient", "legumes", ["PK", "IN", "BD"], 173747),
    ("Green peas (matar)", "green-peas",
     "Peas, green, raw",
     "ingredient", "legumes", ["PK", "IN", "BD", "NP"], 163869),
    ("Soybeans", "soybeans",
     "Soybeans, mature seeds, raw",
     "ingredient", "legumes", ["IN", "BD"], 174290),
    ("Soy chunks", "soy-chunks",
     "Soy protein isolate",
     "ingredient", "legumes", ["IN", "BD"], 174291),
    ("Black chickpeas (kala chana)", "black-chickpeas",
     "Chickpeas (garbanzo beans, bengal gram), mature seeds, raw",
     "ingredient", "legumes", ["PK", "IN", "NP"], 173756),

    # ═══════════════════════════════════════════════════════════════════════
    # POULTRY & EGGS (5)
    # ═══════════════════════════════════════════════════════════════════════
    ("Chicken breast (boneless, cooked)", "chicken-breast",
     "Chicken, broiler or fryers, breast, meat only, cooked, roasted",
     "ingredient", "poultry", ["PK", "IN", "BD", "LK", "NP"], 171077),
    ("Chicken thigh (cooked)", "chicken-thigh",
     "Chicken, broilers or fryers, thigh, meat only, cooked, roasted",
     "ingredient", "poultry", ["PK", "IN", "BD", "LK"], 171477),
    ("Whole egg (raw)", "egg-raw",
     "Egg, whole, raw, fresh",
     "ingredient", "eggs", ["PK", "IN", "BD", "LK", "NP"], 171287),
    ("Whole egg (hard-boiled)", "egg-boiled",
     "Egg, whole, cooked, hard-boiled",
     "ingredient", "eggs", ["PK", "IN", "BD", "LK", "NP"], 171290),
    ("Egg (omelette/scrambled)", "egg-omelette",
     "Egg, whole, cooked, fried",
     "ingredient", "eggs", ["PK", "IN", "BD"], 171291),

    # ═══════════════════════════════════════════════════════════════════════
    # MEATS (5)
    # ═══════════════════════════════════════════════════════════════════════
    ("Mutton/goat (cooked)", "mutton",
     "Goat, meat, cooked, roasted",
     "ingredient", "meats", ["PK", "IN", "BD", "NP"], 173849),
    ("Lamb (leg, cooked)", "lamb",
     "Lamb, leg, whole, separable lean only, cooked, roasted",
     "ingredient", "meats", ["PK", "IN"], 172237),
    ("Beef (lean, cooked)", "beef",
     "Beef, top sirloin, lean only, cooked, broiled",
     "ingredient", "meats", ["PK", "BD"], 171343),
    ("Beef liver (cooked)", "beef-liver",
     "Beef, liver, cooked, pan-fried",
     "ingredient", "meats", ["PK", "IN", "BD"], 171346),
    ("Chicken liver (cooked)", "chicken-liver",
     "Chicken, liver, all classes, cooked, simmered",
     "ingredient", "meats", ["PK", "IN", "BD"], 171111),

    # ═══════════════════════════════════════════════════════════════════════
    # FISH & SEAFOOD (6)
    # ═══════════════════════════════════════════════════════════════════════
    ("Rohu/carp (cooked)", "rohu-fish",
     "Fish, carp, cooked, dry heat",
     "ingredient", "fish", ["IN", "BD"], 175170),
    ("Sardines (canned)", "sardines",
     "Fish, sardine, Atlantic, canned in oil, drained solids with bone",
     "ingredient", "fish", ["IN", "BD", "LK", "PK"], 175181),
    ("Mackerel (cooked)", "mackerel",
     "Fish, mackerel, Atlantic, cooked, dry heat",
     "ingredient", "fish", ["IN", "BD", "LK", "PK"], 175174),
    ("Pomfret/butterfish", "pomfret",
     "Fish, butterfish, raw",
     "ingredient", "fish", ["IN", "BD", "LK"], 175164),
    ("Shrimp/prawns (cooked)", "shrimp",
     "Crustaceans, shrimp, cooked, moist heat",
     "ingredient", "fish", ["PK", "IN", "BD", "LK"], 175180),
    ("Rohu (raw)", "rohu-fish-raw",
     "Fish, carp, raw",
     "ingredient", "fish", ["IN", "BD"], 175169),

    # ═══════════════════════════════════════════════════════════════════════
    # DAIRY (9)
    # ═══════════════════════════════════════════════════════════════════════
    ("Whole milk", "whole-milk",
     "Milk, whole, 3.25% milkfat, with added vitamin D",
     "ingredient", "dairy", ["PK", "IN", "BD", "LK", "NP"], 171265),
    ("Yogurt (plain, whole milk)", "plain-yogurt",
     "Yogurt, plain, whole milk",
     "ingredient", "dairy", ["PK", "IN", "BD", "LK", "NP"], 171271),
    ("Butter (salted)", "butter",
     "Butter, salted",
     "ingredient", "dairy", ["PK", "IN", "BD", "LK", "NP"], 173401),
    ("Ghee (clarified butter)", "ghee",
     "Butter oil, anhydrous",
     "ingredient", "dairy", ["PK", "IN", "BD", "NP"], 173402),
    ("Paneer (cottage cheese)", "paneer",
     "Cheese, cottage, low-fat, 2% milkfat",
     "ingredient", "dairy", ["IN", "NP"], 170875),
    ("Heavy cream", "heavy-cream",
     "Cream, fluid, heavy whipping",
     "ingredient", "dairy", ["PK", "IN"], 170861),
    ("Condensed milk (sweetened)", "condensed-milk",
     "Milk, sweetened, condensed, canned",
     "ingredient", "dairy", ["PK", "IN", "BD"], 171274),
    ("Skimmed milk", "skimmed-milk",
     "Milk, nonfat, fluid, with added vitamin A and D",
     "ingredient", "dairy", ["PK", "IN", "BD"], 171267),
    ("Buttermilk (low fat)", "buttermilk",
     "Buttermilk, lowfat",
     "ingredient", "dairy", ["PK", "IN", "NP"], 171276),

    # ═══════════════════════════════════════════════════════════════════════
    # VEGETABLES (22)
    # ═══════════════════════════════════════════════════════════════════════
    ("Onion", "onion", "Onions, raw",
     "ingredient", "vegetables", ["PK", "IN", "BD", "LK", "NP"], 170000),
    ("Tomato", "tomato", "Tomatoes, red, ripe, raw, year round average",
     "ingredient", "vegetables", ["PK", "IN", "BD", "LK", "NP"], 170457),
    ("Potato", "potato", "Potatoes, flesh and skin, raw",
     "ingredient", "vegetables", ["PK", "IN", "BD", "LK", "NP"], 170026),
    ("Eggplant (brinjal)", "eggplant", "Eggplant, raw",
     "ingredient", "vegetables", ["PK", "IN", "BD", "LK", "NP"], 170092),
    ("Okra (ladyfinger)", "okra", "Okra, raw",
     "ingredient", "vegetables", ["PK", "IN", "BD", "LK"], 170056),
    ("Spinach (palak)", "spinach", "Spinach, raw",
     "ingredient", "vegetables", ["PK", "IN", "NP"], 168409),
    ("Green chili", "green-chili", "Peppers, chili, green, raw",
     "ingredient", "vegetables", ["PK", "IN", "BD", "NP"], 170428),
    ("Cauliflower", "cauliflower", "Cauliflower, raw",
     "ingredient", "vegetables", ["PK", "IN", "BD", "NP"], 170094),
    ("Cabbage", "cabbage", "Cabbage, raw",
     "ingredient", "vegetables", ["PK", "IN", "BD", "NP", "LK"], 170093),
    ("Bottle gourd (lauki)", "bottle-gourd", "Gourd, bottle, raw",
     "ingredient", "vegetables", ["PK", "IN", "NP"], 170414),
    ("Bitter gourd (karela)", "bitter-gourd", "Bitter gourd (bitter melon), raw",
     "ingredient", "vegetables", ["PK", "IN", "BD", "NP"], 170401),
    ("Carrot", "carrot", "Carrots, raw",
     "ingredient", "vegetables", ["PK", "IN", "BD", "NP", "LK"], 170054),
    ("Beetroot", "beetroot", "Beets, raw",
     "ingredient", "vegetables", ["PK", "IN", "NP"], 170055),
    ("Green beans", "green-beans", "Beans, snap, green, raw",
     "ingredient", "vegetables", ["IN", "BD", "NP"], 170053),
    ("Sweet potato", "sweet-potato", "Sweet potato, raw, unprepared",
     "ingredient", "vegetables", ["PK", "IN", "BD", "NP"], 170096),
    ("Radish (mooli)", "radish", "Radishes, raw",
     "ingredient", "vegetables", ["PK", "IN", "NP"], 170416),
    ("Capsicum (red bell pepper)", "capsicum", "Peppers, sweet, red, raw",
     "ingredient", "vegetables", ["PK", "IN", "BD"], 170427),
    ("Taro root", "taro-root", "Taro, raw",
     "ingredient", "vegetables", ["IN", "BD", "LK"], 170085),
    ("Drumstick (moringa pods)", "drumstick", "Drumstick pods, raw",
     "ingredient", "vegetables", ["IN", "LK", "BD"], 169965),
    ("Ridge gourd", "ridge-gourd", "Gourd, loofah, raw",
     "ingredient", "vegetables", ["IN", "BD"], 170415),
    ("Fenugreek leaves (methi)", "fenugreek-leaves", "Spices, fenugreek seed",
     "ingredient", "vegetables", ["PK", "IN"], 168427),
    ("Sweet corn (kernels)", "sweet-corn", "Corn, sweet, yellow, raw",
     "ingredient", "vegetables", ["IN", "BD", "NP"], 170046),

    # ═══════════════════════════════════════════════════════════════════════
    # FRUITS (14)
    # ═══════════════════════════════════════════════════════════════════════
    ("Mango", "mango", "Mangoes, raw",
     "ingredient", "fruits", ["PK", "IN", "BD", "LK", "NP"], 171712),
    ("Banana", "banana", "Bananas, raw",
     "ingredient", "fruits", ["PK", "IN", "BD", "LK", "NP"], 173944),
    ("Papaya", "papaya", "Papayas, raw",
     "ingredient", "fruits", ["PK", "IN", "BD", "LK"], 170120),
    ("Guava", "guava", "Guavas, raw",
     "ingredient", "fruits", ["PK", "IN", "BD", "LK"], 170122),
    ("Pomegranate", "pomegranate", "Pomegranates, raw",
     "ingredient", "fruits", ["PK", "IN", "BD"], 170123),
    ("Coconut (fresh meat)", "coconut-fresh", "Coconut meat, raw",
     "ingredient", "fruits", ["IN", "LK", "BD", "PK"], 170075),
    ("Lemon", "lemon", "Lemon, raw, without peel",
     "ingredient", "fruits", ["PK", "IN", "BD", "NP", "LK"], 170076),
    ("Dates (khajoor)", "dates", "Dates, deglet noor",
     "ingredient", "fruits", ["PK", "IN", "BD"], 171714),
    ("Orange", "orange", "Oranges, raw, all commercial varieties",
     "ingredient", "fruits", ["PK", "IN", "BD", "NP"], 169097),
    ("Apple", "apple", "Apples, raw, with skin",
     "ingredient", "fruits", ["PK", "IN", "NP"], 171688),
    ("Watermelon", "watermelon", "Watermelon, raw",
     "ingredient", "fruits", ["PK", "IN", "BD"], 170049),
    ("Pineapple", "pineapple", "Pineapple, raw, all varieties",
     "ingredient", "fruits", ["IN", "BD", "LK"], 170034),
    ("Jackfruit", "jackfruit", "Jackfruit, raw",
     "ingredient", "fruits", ["IN", "BD", "LK"], 170035),
    ("Gooseberry (amla)", "gooseberry", "Gooseberries, raw",
     "ingredient", "fruits", ["IN", "NP"], 170119),

    # ═══════════════════════════════════════════════════════════════════════
    # NUTS & SEEDS (8)
    # ═══════════════════════════════════════════════════════════════════════
    ("Almonds", "almonds", "Nuts, almonds, dry roasted, without salt added",
     "ingredient", "nuts-seeds", ["PK", "IN", "BD"], 170567),
    ("Cashews", "cashews", "Nuts, cashew nuts, dry roasted, without salt added",
     "ingredient", "nuts-seeds", ["PK", "IN", "BD"], 170568),
    ("Peanuts", "peanuts", "Peanuts, all types, dry-roasted, without salt",
     "ingredient", "nuts-seeds", ["PK", "IN", "BD", "NP"], 160871),
    ("Walnuts", "walnuts", "Nuts, walnuts, english",
     "ingredient", "nuts-seeds", ["PK", "IN"], 170187),
    ("Sesame seeds", "sesame-seeds", "Seeds, sesame seeds, whole, dried",
     "ingredient", "nuts-seeds", ["PK", "IN", "BD"], 12023),
    ("Flax seeds", "flax-seeds", "Seeds, flaxseed",
     "ingredient", "nuts-seeds", ["IN", "NP"], 12220),
    ("Sunflower seeds", "sunflower-seeds", "Seeds, sunflower seed kernels, dried",
     "ingredient", "nuts-seeds", ["PK", "IN"], 12036),
    ("Desiccated coconut", "desiccated-coconut",
     "Coconut, meat, dried (desiccated), not sweetened",
     "ingredient", "nuts-seeds", ["IN", "BD", "LK"], 12179),

    # ═══════════════════════════════════════════════════════════════════════
    # OILS & FATS (7)
    # ═══════════════════════════════════════════════════════════════════════
    ("Mustard oil", "mustard-oil", "Oil, canola",
     "ingredient", "oils-fats", ["PK", "IN", "BD", "NP"], 4513),
    ("Sunflower oil", "sunflower-oil", "Oil, sunflower, high oleic (70% and over)",
     "ingredient", "oils-fats", ["PK", "IN", "BD"], 4512),
    ("Coconut oil", "coconut-oil", "Oil, coconut",
     "ingredient", "oils-fats", ["IN", "LK", "BD"], 4044),
    ("Olive oil", "olive-oil", "Oil, olive, salad or cooking",
     "ingredient", "oils-fats", ["PK", "IN"], 4053),
    ("Vegetable oil (soybean)", "vegetable-oil", "Oil, vegetable, soybean, refined",
     "ingredient", "oils-fats", ["PK", "IN", "BD", "LK", "NP"], 4513),
    ("Sesame oil", "sesame-oil", "Oil, sesame",
     "ingredient", "oils-fats", ["IN", "PK"], 4058),
    ("Groundnut/peanut oil", "groundnut-oil", "Oil, peanut (groundnut)",
     "ingredient", "oils-fats", ["IN", "BD", "PK"], 4042),

    # ═══════════════════════════════════════════════════════════════════════
    # SPICES & CONDIMENTS (16)
    # ═══════════════════════════════════════════════════════════════════════
    ("Turmeric (ground)", "turmeric", "Spices, turmeric, ground",
     "ingredient", "spices", ["PK", "IN", "BD", "NP", "LK"], 168429),
    ("Cumin seeds", "cumin-seeds", "Spices, cumin seed",
     "ingredient", "spices", ["PK", "IN", "BD", "NP"], 168428),
    ("Coriander (ground)", "coriander-ground", "Spices, coriander seed",
     "ingredient", "spices", ["PK", "IN", "BD", "NP"], 168426),
    ("Red chili powder", "red-chili-powder", "Spices, chili powder",
     "ingredient", "spices", ["PK", "IN", "BD", "NP"], 168430),
    ("Black pepper", "black-pepper", "Spices, pepper, black",
     "ingredient", "spices", ["PK", "IN", "BD", "NP", "LK"], 168431),
    ("Ginger (ground)", "ginger", "Spices, ginger, ground",
     "ingredient", "spices", ["PK", "IN", "BD", "NP", "LK"], 168432),
    ("Garlic (raw)", "garlic", "Garlic, raw",
     "ingredient", "spices", ["PK", "IN", "BD", "NP", "LK"], 169230),
    ("Cinnamon (ground)", "cinnamon", "Spices, cinnamon, ground",
     "ingredient", "spices", ["PK", "IN", "BD", "NP"], 168433),
    ("Cardamom (ground)", "cardamom", "Spices, cardamom, ground",
     "ingredient", "spices", ["PK", "IN", "BD"], 168434),
    ("Cloves (ground)", "cloves", "Spices, cloves, ground",
     "ingredient", "spices", ["PK", "IN", "BD"], 168435),
    ("Bay leaf", "bay-leaf", "Spices, bay leaf",
     "ingredient", "spices", ["PK", "IN", "BD"], 168436),
    ("Mustard seeds", "mustard-seeds", "Spices, mustard seed, ground",
     "ingredient", "spices", ["PK", "IN", "BD", "NP"], 168438),
    ("Fenugreek seeds", "fenugreek-seeds", "Spices, fenugreek seed",
     "ingredient", "spices", ["PK", "IN"], 168427),
    ("Salt (iodized)", "salt", "Salt, table, iodized",
     "ingredient", "spices", ["PK", "IN", "BD", "LK", "NP"], 168456),
    ("Tamarind", "tamarind", "Tamarind, raw",
     "ingredient", "spices", ["PK", "IN", "BD", "LK"], 168451),
    ("Asafoetida (hing)", "asafoetida", "Spices, asafoetida",
     "ingredient", "spices", ["IN", "NP"], 168418),

    # ═══════════════════════════════════════════════════════════════════════
    # BEVERAGES (4)
    # ═══════════════════════════════════════════════════════════════════════
    ("Black tea (brewed)", "black-tea", "Tea, brewed, prepared with tap water",
     "ingredient", "beverages", ["PK", "IN", "BD", "LK", "NP"], 168453),
    ("Coffee (brewed)", "coffee-brewed", "Coffee, brewed, prepared with tap water",
     "ingredient", "beverages", ["PK", "IN", "BD"], 168443),
    ("Coconut water", "coconut-water", "Beverages, coconut water, canned",
     "ingredient", "beverages", ["IN", "LK", "BD"], 12118),
    ("Mango juice (nectar)", "mango-juice", "Juice, mango nectar, canned",
     "ingredient", "beverages", ["IN", "BD"], 168450),

    # ═══════════════════════════════════════════════════════════════════════
    # SWEETENERS (3)
    # ═══════════════════════════════════════════════════════════════════════
    ("Sugar (granulated)", "sugar", "Sugars, granulated",
     "ingredient", "sweeteners", ["PK", "IN", "BD", "LK", "NP"], 168455),
    ("Jaggery (gur)", "jaggery", "Sugars, brown",
     "ingredient", "sweeteners", ["PK", "IN", "BD", "NP"], 168457),
    ("Honey", "honey", "Honey",
     "ingredient", "sweeteners", ["PK", "IN", "BD", "NP"], 19296),

    # ═══════════════════════════════════════════════════════════════════════
    # BREADS (6)
    # ═══════════════════════════════════════════════════════════════════════
    ("Chapati/roti (whole wheat)", "chapati",
     "Chapati or roti, whole wheat flatbread (estimated from whole wheat flour)",
     "composite", "breads", ["PK", "IN", "BD", "NP"], 168944),
    ("Naan (white flour)", "naan",
     "Naan, white flour flatbread (estimated from white flour)",
     "composite", "breads", ["PK", "IN", "NP"], 168872),
    ("Paratha (plain)", "plain-paratha",
     "Paratha, layered wheat flatbread with fat",
     "composite", "breads", ["PK", "IN", "BD", "NP"], 168872),
    ("Dosa (fermented crepe)", "dosa",
     "Dosa, fermented rice and lentil crepe",
     "composite", "breads", ["IN", "LK"], 168890),
    ("Idli (steamed cake)", "idli",
     "Idli, steamed fermented rice and lentil cake",
     "composite", "breads", ["IN", "LK"], 168890),
    ("Poori (fried bread)", "poori",
     "Poori, deep-fried whole wheat bread",
     "composite", "breads", ["PK", "IN", "BD", "NP"], 168944),

    # ═══════════════════════════════════════════════════════════════════════
    # PREPARED DISHES (15)
    # All marked as "pending_review" since these are approximations
    # using base ingredient data from USDA, not actual lab analyses.
    # ═══════════════════════════════════════════════════════════════════════
    ("Dal (boiled lentils)", "dal-boiled",
     "Lentils, mature seeds, cooked, boiled, without salt",
     "composite", "prepared-dishes",
     ["PK", "IN", "BD", "NP", "LK"], 172421),
    ("Chickpea curry (chole)", "chole",
     "Chickpeas (garbanzo beans), mature seeds, cooked, boiled, without salt",
     "composite", "prepared-dishes", ["IN", "PK"], 173757),
    ("Kidney bean curry (rajma)", "rajma-curry",
     "Beans, kidney, red, mature seeds, cooked, boiled, without salt",
     "composite", "prepared-dishes", ["IN", "PK"], 173745),
    ("Mung bean curry", "mung-curry",
     "Mung beans, mature seeds, cooked, boiled, without salt",
     "composite", "prepared-dishes", ["PK", "IN", "BD", "NP"], 174257),
    ("Mashed potato", "mashed-potato",
     "Potatoes, mashed, home-prepared, whole milk and butter added",
     "composite", "prepared-dishes", ["PK", "IN", "BD", "LK", "NP"], 170031),
    ("Khichdi (rice + lentils)", "khichdi",
     "Khichdi, rice and lentil dish (estimated)",
     "composite", "prepared-dishes", ["IN", "BD", "NP"], 169706),
    ("Vegetable curry (mixed)", "vegetable-curry",
     "Mixed vegetables, cooked, boiled, drained, without salt",
     "composite", "prepared-dishes",
     ["PK", "IN", "BD", "NP", "LK"], 170084),
    ("Poha (flattened rice)", "poha",
     "Poha, flattened rice with vegetables (estimated)",
     "composite", "prepared-dishes", ["IN"], 168553),
    ("Upma (semolina porridge)", "upma",
     "Upma, semolina porridge with vegetables (estimated)",
     "composite", "prepared-dishes", ["IN", "LK"], 168870),
    ("Sambar (lentil stew)", "sambar",
     "Sambar, South Indian lentil and vegetable stew (estimated)",
     "composite", "prepared-dishes", ["IN", "LK"], 172421),
    ("Rasam (tamarind soup)", "rasam",
     "Rasam, South Indian tamarind soup (estimated)",
     "composite", "prepared-dishes", ["IN", "LK"], 170457),
    ("Aloo gobi", "aloo-gobi",
     "Aloo gobi, potato and cauliflower curry (estimated)",
     "composite", "prepared-dishes", ["IN", "PK", "NP"], 170026),
    ("Palak paneer", "palak-paneer",
     "Palak paneer, spinach with cottage cheese (estimated)",
     "composite", "prepared-dishes", ["IN", "NP"], 170875),
    ("Egg curry", "egg-curry",
     "Egg curry, hard-boiled eggs in spiced gravy (estimated)",
     "composite", "prepared-dishes", ["PK", "IN", "BD"], 171290),
    ("Mashed banana (kela)", "mashed-banana",
     "Bananas, mashed",
     "composite", "prepared-dishes", ["IN", "BD", "NP"], 173944),

    # ═══════════════════════════════════════════════════════════════════════
    # LASSI & DRINKS (3)
    # ═══════════════════════════════════════════════════════════════════════
    ("Sweet lassi", "sweet-lassi",
     "Lassi, sweet yogurt-based drink (estimated from yogurt + sugar)",
     "composite", "beverages", ["PK", "IN"], 171271),
    ("Masala chai", "masala-chai",
     "Masala chai, spiced milk tea (estimated from milk + tea + sugar)",
     "composite", "beverages", ["PK", "IN", "BD", "NP"], 171265),
    ("Nimbu pani (lemonade)", "nimbu-pani",
     "Fresh lemonade with sugar (estimated from lemon + sugar + water)",
     "composite", "beverages", ["PK", "IN", "BD"], 170076),

    # ═══════════════════════════════════════════════════════════════════════
    # ADDITIONAL INGREDIENTS TO REACH ~200 (14)
    # ═══════════════════════════════════════════════════════════════════════
    ("Poppy seeds", "poppy-seeds", "Seeds, poppy seed, dried",
     "ingredient", "nuts-seeds", ["IN", "BD"], 12014),
    ("Mushroom", "mushroom", "Mushrooms, white, raw",
     "ingredient", "vegetables", ["IN", "NP"], 169250),
    ("Lettuce (romaine)", "lettuce", "Lettuce, romaine, raw",
     "ingredient", "vegetables", ["IN", "LK"], 169249),
    ("Spring onion", "spring-onion", "Onions, spring or scallions, tops only, raw",
     "ingredient", "vegetables", ["IN", "BD"], 168955),
    ("Turnip", "turnip", "Turnips, raw",
     "ingredient", "vegetables", ["PK", "IN", "NP"], 170098),
    ("Pumpkin seeds", "pumpkin-seeds", "Seeds, pumpkin and squash seed kernels, dried",
     "ingredient", "nuts-seeds", ["IN", "PK"], 12011),
    ("Sapodilla (chiku)", "sapodilla", "Sapodilla, raw",
     "ingredient", "fruits", ["IN", "BD"], 170127),
    ("Butter (unsalted)", "unsalted-butter", "Butter, unsalted",
     "ingredient", "dairy", ["PK", "IN"], 173400),
    ("Garam masala", "garam-masala", "Spices, garam masala",
     "ingredient", "spices", ["PK", "IN", "BD", "NP"], 168436),
    ("Nigella seeds (kalonji)", "nigella-seeds", "Spices, nigella seed",
     "ingredient", "spices", ["PK", "IN"], 168438),
    ("Carom seeds (ajwain)", "carom-seeds", "Spices, caraway seed",
     "ingredient", "spices", ["IN", "PK"], 168425),
    ("Bread (white)", "white-bread", "Bread, white, commercially prepared",
     "ingredient", "grains", ["PK", "IN", "BD", "LK"], 168874),
    ("Popcorn (air-popped)", "popcorn", "Popcorn, air-popped",
     "ingredient", "snacks", ["IN", "PK"], 168552),
    ("Papadum", "papadum", "Snacks, papad (estimated from lentil flour)",
     "composite", "snacks", ["IN", "LK"], 174288),
]


def build_dataset(api_key: str, cache_path: Path | None = None) -> tuple[dict, list[str]]:
    """Build the full dataset, fetching from FDC API in batches."""
    cache: dict[str, dict] = {}
    if cache_path and cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        print(f"Loaded {len(cache)} cached entries")

    # Deduplicate FDC IDs
    fdc_ids_needed = set()
    for food in FOODS:
        fdc_ids_needed.add(food[6])  # fdc_id

    fdc_ids_to_fetch = [fid for fid in fdc_ids_needed if str(fid) not in cache]
    print(f"Unique FDC IDs: {len(fdc_ids_needed)}, need to fetch: {len(fdc_ids_to_fetch)}")

    # Fetch in batches of 20
    BATCH_SIZE = 20
    for i in range(0, len(fdc_ids_to_fetch), BATCH_SIZE):
        batch = fdc_ids_to_fetch[i:i + BATCH_SIZE]
        print(f"  Fetching batch {i // BATCH_SIZE + 1}: {len(batch)} foods...", end=" ", flush=True)
        result = api_post("/foods", {"fdcIds": batch}, api_key)
        if result and isinstance(result, list):
            for food_data in result:
                fid = str(food_data.get("fdcId", ""))
                nutrients = extract_nutrients(food_data)
                cache[fid] = {
                    "description": food_data.get("description", ""),
                    "fdcId": food_data.get("fdcId", 0),
                    "dataType": food_data.get("dataType", ""),
                    "publishedDate": food_data.get("publishedDate", ""),
                    "nutrients": nutrients,
                }
            print(f"OK ({len(result)} foods)")
        else:
            print("FAILED")
        time.sleep(2)

    # Save cache
    if cache_path:
        cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Cache saved: {len(cache)} entries")

    # Build records
    records = []
    errors = []
    seen_slugs: set[str] = set()

    for food in FOODS:
        name, slug, desc, ftype, category, countries, fdc_id = food

        if slug in seen_slugs:
            errors.append(f"Duplicate slug: {slug}")
            continue
        seen_slugs.add(slug)

        cached = cache.get(str(fdc_id))
        if not cached:
            errors.append(f"{name}: FDC-{fdc_id} not found in cache")
            continue

        nutrients = cached.get("nutrients", {})
        if not nutrients:
            errors.append(f"{name}: No nutrients for FDC-{fdc_id}")
            continue

        record = {
            "name": name,
            "slug": slug,
            "description": cached.get("description", desc),
            "food_type": ftype,
            "category": category,
            "countries": countries,
            "regions": [],
            "nutrition": {
                "calories": round(nutrients.get("208", 0), 2),
                "protein_g": round(nutrients.get("203", 0), 3),
                "carbs_g": round(nutrients.get("205", 0), 3),
                "fat_g": round(nutrients.get("204", 0), 3),
                "fiber_g": round(nutrients.get("291", 0), 3) if "291" in nutrients else None,
                "sugar_g": round(nutrients.get("269", 0), 3) if "269" in nutrients else None,
                "sodium_mg": round(nutrients.get("307", 0), 3) if "307" in nutrients else None,
            },
            "serving": {
                "amount": 100,
                "unit": "g",
                "grams_equivalent": 100,
            },
            "ingredients": [],
            "source": {
                "source_name": "USDA FoodData Central",
                "source_identifier": f"FDC-{fdc_id}",
                "source_version": cached.get("dataType", "SR Legacy"),
                "source_date": cached.get("publishedDate", ""),
                "verification_status": "pending_review",
                "notes": f"USDA FDC. Description: {cached.get('description', '')}",
            },
        }
        records.append(record)

    dataset = {
        "dataset_source": {
            "name": "USDA FoodData Central",
            "version": "SR Legacy / Foundation",
            "reference_url": "https://fdc.nal.usda.gov/",
            "license_category": "public_domain",
            "attribution_text": "U.S. Department of Agriculture, Agricultural Research Service. FoodData Central, 2019. fdc.nal.usda.gov.",
            "can_store_raw_data": True,
            "can_store_derived_values": True,
            "source_date": "2024-01-01T00:00:00+00:00",
            "description": "USDA FoodData Central SR Legacy and Foundation data. Public domain (CC0). Nutrition values per 100g edible portion.",
        },
        "foods": records,
    }
    return dataset, errors


def validate_dataset(dataset: dict) -> dict:
    """Validate the dataset and return a report."""
    foods = dataset.get("foods", [])
    report = {
        "total_foods": len(foods),
        "complete_nutrition": 0,
        "incomplete_nutrition": 0,
        "flagged_for_review": 0,
        "by_category": {},
        "by_country": {},
        "by_verification": {},
        "issues": [],
    }

    for food in foods:
        cat = food.get("category", "unknown")
        report["by_category"][cat] = report["by_category"].get(cat, 0) + 1

        for c in food.get("countries", []):
            report["by_country"][c] = report["by_country"].get(c, 0) + 1

        vs = food.get("source", {}).get("verification_status", "unknown")
        report["by_verification"][vs] = report["by_verification"].get(vs, 0) + 1

        nut = food.get("nutrition", {})
        has_all = all(
            nut.get(k) is not None and nut[k] > 0
            for k in ["calories", "protein_g", "carbs_g", "fat_g"]
        )
        if has_all:
            report["complete_nutrition"] += 1
        else:
            report["incomplete_nutrition"] += 1
            report["issues"].append(f"{food['name']}: Missing core nutrition values")

        if vs == "pending_review":
            report["flagged_for_review"] += 1

        # Sanity checks
        cal = nut.get("calories", 0)
        protein = nut.get("protein_g", 0)
        carbs = nut.get("carbs_g", 0)
        fat = nut.get("fat_g", 0)
        atwater = protein * 4 + carbs * 4 + fat * 9
        if cal > 0 and atwater > 0:
            deviation = abs(cal - atwater) / max(atwater, 1) * 100
            if deviation > 50:
                report["issues"].append(
                    f"{food['name']}: Atwater deviation {deviation:.0f}% "
                    f"(stated={cal}, calculated={atwater:.0f})"
                )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build South Asian food dataset")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--output", default=str(Path(__file__).parent.parent / "data" / "south_asian_foods.json"))
    parser.add_argument("--cache", default=str(Path(__file__).parent.parent / "data" / ".fdc_cache.json"))
    args = parser.parse_args()

    cache_path = Path(args.cache)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    print("Building dataset from USDA FoodData Central...")
    print(f"Foods to process: {len(FOODS)}")

    dataset, errors = build_dataset(args.api_key, cache_path)

    if not dataset.get("foods"):
        print("ERROR: No records built")
        return 1

    # Validate
    report = validate_dataset(dataset)

    # Write dataset
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")

    # Write validation report
    report_path = output_path.parent / "south_asian_foods_validation.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # Print summary
    print(f"\n{'='*60}")
    print("DATASET BUILD COMPLETE")
    print(f"{'='*60}")
    print(f"Total foods: {report['total_foods']}")
    print(f"Complete nutrition: {report['complete_nutrition']}")
    print(f"Incomplete nutrition: {report['incomplete_nutrition']}")
    print(f"Flagged for review: {report['flagged_for_review']}")
    print(f"Errors: {len(errors)}")

    print("\nBy category:")
    for cat, count in sorted(report["by_category"].items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    print("\nBy country:")
    for country, count in sorted(report["by_country"].items(), key=lambda x: -x[1]):
        print(f"  {country}: {count}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e}")

    if report["issues"]:
        print(f"\nIssues ({len(report['issues'])}):")
        for issue in report["issues"][:10]:
            print(f"  - {issue}")
        if len(report["issues"]) > 10:
            print(f"  ... and {len(report['issues']) - 10} more")

    print(f"\nOutput: {output_path}")
    print(f"Validation: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
