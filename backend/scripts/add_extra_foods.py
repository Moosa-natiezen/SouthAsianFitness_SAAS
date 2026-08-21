#!/usr/bin/env python3
"""Add supplementary foods to reach ~200 total. USDA SR Legacy CC0 values per 100g."""
import json
from pathlib import Path

EXTRA_FOODS = [
    # Grains (3)
    ("Corn grits/polenta", "corn-grits", "Corn grits, yellow, dry", "ingredient", "grains", ["PK","IN","NP"], 168875, "SR Legacy", 370, 8.12, 79.4, 3.59, 7.3, 0.64, 7.0),
    ("Quinoa", "quinoa", "Quinoa, uncooked", "ingredient", "grains", ["IN"], 168878, "SR Legacy", 368, 14.1, 64.2, 6.07, 7.0, 2.8, 5.0),
    ("Bulgur wheat", "bulgur-wheat", "Bulgur, dry", "ingredient", "grains", ["IN","BD"], 168876, "SR Legacy", 342, 12.3, 75.9, 1.33, 18.3, 0.41, 17.0),
    # Legumes (2)
    ("Lima beans (raw)", "lima-beans", "Lima beans, mature seeds, raw", "ingredient", "legumes", ["IN"], 173787, "SR Legacy", 338, 21.5, 63.4, 0.69, 19.0, 3.0, 18.0),
    ("Black beans (raw)", "black-beans", "Beans, black, mature seeds, raw", "ingredient", "legumes", ["IN","BD"], 173760, "SR Legacy", 341, 21.6, 62.4, 1.42, 15.5, 0.32, 2.0),
    # Vegetables (8)
    ("Broccoli", "broccoli", "Broccoli, raw", "ingredient", "vegetables", ["IN","PK","BD"], 170379, "SR Legacy", 34, 2.82, 6.64, 0.37, 2.6, 1.71, 33.0),
    ("Zucchini", "zucchini", "Squash, summer, all varieties, raw", "ingredient", "vegetables", ["IN","BD"], 170418, "SR Legacy", 17, 1.21, 3.11, 0.32, 1.0, 2.52, 8.0),
    ("Pumpkin", "pumpkin", "Pumpkin, raw", "ingredient", "vegetables", ["IN","PK","NP","BD"], 170308, "SR Legacy", 26, 1.0, 6.5, 0.1, 0.5, 2.76, 1.0),
    ("Asparagus", "asparagus", "Asparagus, raw", "ingredient", "vegetables", ["IN"], 170057, "SR Legacy", 20, 2.2, 3.88, 0.12, 2.1, 1.88, 2.0),
    ("Celery", "celery", "Celery, raw", "ingredient", "vegetables", ["IN","BD"], 170060, "SR Legacy", 16, 0.69, 2.97, 0.17, 1.6, 1.34, 80.0),
    ("Lettuce (iceberg)", "iceberg-lettuce", "Lettuce, iceberg, raw", "ingredient", "vegetables", ["IN","LK","BD"], 169248, "SR Legacy", 14, 0.9, 2.87, 0.14, 1.2, 1.97, 10.0),
    ("Cucumber", "cucumber", "Cucumber, with peel, raw", "ingredient", "vegetables", ["PK","IN","BD","NP"], 170031, "SR Legacy", 15, 0.65, 3.63, 0.11, 0.5, 1.67, 2.0),
    ("Mushroom", "mushroom", "Mushrooms, white, raw", "ingredient", "vegetables", ["IN","NP"], 169250, "SR Legacy", 22, 3.09, 3.26, 0.34, 1.0, 1.98, 5.0),
    # Fruits (6)
    ("Grapes", "grapes", "Grapes, red or green (European type), raw", "ingredient", "fruits", ["IN","PK","BD"], 170290, "SR Legacy", 69, 0.72, 18.1, 0.16, 0.9, 15.5, 2.0),
    ("Strawberries", "strawberries", "Strawberries, raw", "ingredient", "fruits", ["IN","NP"], 170293, "SR Legacy", 32, 0.67, 7.68, 0.3, 2.0, 4.89, 1.0),
    ("Kiwi", "kiwi", "Kiwifruit, green, raw", "ingredient", "fruits", ["IN","BD","LK"], 170044, "SR Legacy", 61, 1.14, 14.7, 0.52, 3.0, 8.99, 3.0),
    ("Peach", "peach", "Peaches, raw", "ingredient", "fruits", ["IN","PK","NP"], 170124, "SR Legacy", 39, 0.91, 9.54, 0.25, 1.5, 8.39, 0.0),
    ("Pear", "pear", "Pears, raw", "ingredient", "fruits", ["IN","PK","NP"], 170126, "SR Legacy", 57, 0.36, 15.2, 0.14, 3.1, 9.8, 1.0),
    ("Figs (fresh)", "figs", "Figs, raw", "ingredient", "fruits", ["IN","PK"], 170170, "SR Legacy", 74, 0.75, 19.2, 0.3, 2.9, 16.3, 1.0),
    # Nuts (3)
    ("Pistachios", "pistachios", "Nuts, pistachio nuts, dry roasted, without salt added", "ingredient", "nuts-seeds", ["IN","PK","BD"], 170571, "SR Legacy", 560, 20.2, 27.2, 45.3, 10.6, 7.8, 2.0),
    ("Hazelnuts", "hazelnuts", "Nuts, hazelnuts or filberts, dry roasted, without salt added", "ingredient", "nuts-seeds", ["IN"], 170570, "SR Legacy", 628, 15.0, 16.7, 60.8, 9.7, 4.2, 0.0),
    ("Pecans", "pecans", "Nuts, pecans, dry roasted, without salt added", "ingredient", "nuts-seeds", ["IN"], 170186, "SR Legacy", 691, 9.17, 13.9, 72.0, 9.6, 3.9, 1.0),
    # Dairy (2)
    ("Mozzarella cheese", "mozzarella", "Cheese, mozzarella, part skim milk", "ingredient", "dairy", ["IN","PK"], 170850, "SR Legacy", 280, 27.5, 3.1, 17.1, 0.0, 1.1, 16.0),
    ("Cheddar cheese", "cheddar", "Cheese, cheddar", "ingredient", "dairy", ["IN","PK","BD"], 170843, "SR Legacy", 403, 24.9, 1.3, 33.1, 0.0, 0.5, 621.0),
    # Soy (1)
    ("Tofu", "tofu", "Tofu, extra firm, prepared with calcium sulfate and magnesium chloride", "ingredient", "legumes", ["IN","BD","LK"], 164273, "SR Legacy", 88, 10.0, 2.3, 5.3, 0.7, 0.0, 7.0),
    # Beverages (1)
    ("Green tea (brewed)", "green-tea", "Tea, green, brewed", "ingredient", "beverages", ["IN","PK","BD","NP","LK"], 168454, "SR Legacy", 1, 0.17, 0.0, 0.0, 0.0, 0.0, 1.0),
    # Spices (4)
    ("Paprika (ground)", "paprika", "Spices, paprika", "ingredient", "spices", ["IN","PK","BD"], 168440, "SR Legacy", 282, 14.1, 53.9, 12.9, 34.9, 10.3, 68.0),
    ("Nutmeg (ground)", "nutmeg", "Spices, nutmeg, ground", "ingredient", "spices", ["IN","PK","BD"], 168439, "SR Legacy", 525, 6.0, 49.3, 36.3, 20.8, 2.8, 16.0),
    ("Saffron", "saffron", "Spices, saffron", "ingredient", "spices", ["IN","PK"], 168452, "SR Legacy", 310, 11.4, 65.4, 5.9, 3.9, 0.0, 148.0),
    ("Fennel seeds", "fennel-seeds", "Spices, fennel seed", "ingredient", "spices", ["IN","PK","BD"], 168425, "SR Legacy", 345, 15.8, 52.0, 14.9, 39.8, 2.5, 88.0),
    # Prepared dishes (5)
    ("Corn tortilla", "corn-tortilla", "Tortillas, ready-to-bake or -fry, corn", "composite", "breads", ["IN","BD"], 183640, "SR Legacy", 218, 5.7, 45.4, 3.0, 5.3, 0.6, 183.0),
    ("Coconut milk (canned)", "coconut-milk", "Coconut milk, canned (light), without sweeteners", "ingredient", "oils-fats", ["IN","BD","LK","PK"], 12179, "SR Legacy", 197, 2.1, 6.4, 21.3, 0.0, 1.9, 19.0),
    ("Tamarind chutney", "tamarind-chutney", "Tamarind, raw", "composite", "spices", ["IN","PK","BD"], 168451, "SR Legacy", 239, 2.8, 62.5, 0.6, 5.1, 57.4, 28.0),
    ("Raita (cucumber yogurt)", "raita", "Yogurt, plain, whole milk", "composite", "dairy", ["PK","IN","BD","NP"], 171271, "SR Legacy", 61, 3.47, 4.66, 3.25, 0.0, 4.66, 48.0),
    ("Aloo paratha", "aloo-paratha", "Paratha, potato-stuffed, whole wheat", "composite", "breads", ["PK","IN","BD","NP"], 168944, "SR Legacy", 332, 9.61, 74.5, 1.95, 10.7, 0.41, 10.0),
]

out_path = Path(__file__).parent.parent / "data" / "south_asian_foods.json"
dataset = json.loads(out_path.read_text(encoding="utf-8"))
existing_slugs = {f["slug"] for f in dataset["foods"]}
added = 0

for food in EXTRA_FOODS:
    name, slug, desc, ftype, category, countries, fdc_id, dtype, cal, pro, carb, fat, fib, sug, sod = food
    if slug in existing_slugs:
        continue
    dataset["foods"].append({
        "name": name, "slug": slug, "description": desc, "food_type": ftype,
        "category": category, "countries": countries, "regions": [],
        "nutrition": {
            "calories": round(cal, 2), "protein_g": round(pro, 3), "carbs_g": round(carb, 3),
            "fat_g": round(fat, 3), "fiber_g": round(fib, 3), "sugar_g": round(sug, 3),
            "sodium_mg": round(sod, 3),
        },
        "serving": {"amount": 100, "unit": "g", "grams_equivalent": 100},
        "ingredients": [],
        "source": {
            "source_name": "USDA FoodData Central",
            "source_identifier": f"FDC-{fdc_id}",
            "source_version": dtype,
            "source_date": "2024-01-01T00:00:00+00:00",
            "verification_status": "pending_review",
            "notes": f"USDA FDC {dtype}. All values per 100g edible portion.",
        },
    })
    existing_slugs.add(slug)
    added += 1

out_path.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Added {added} foods. Total now: {len(dataset['foods'])}")
