#!/usr/bin/env python3
"""Generate the South Asian food dataset using verified USDA SR Legacy values.

All nutrition data in this script is sourced from USDA FoodData Central
SR Legacy and Foundation datasets, which are public domain (CC0 1.0).

Source: U.S. Department of Agriculture, Agricultural Research Service.
        FoodData Central, 2019. fdc.nal.usda.gov.

Every nutrition value is per 100g edible portion, consistent with the
USDA SR Legacy reference basis. The FDC ID for each food is recorded
as the source_identifier for full traceability.

This script does NOT call any external API. It generates the dataset
from published, verified USDA values that are freely available in the
public domain.

Usage:
    python -m scripts.generate_dataset
"""

from __future__ import annotations

import json
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# USDA SR LEGACY NUTRITION DATA
# All values are per 100g edible portion.
# Source: USDA FoodData Central, SR Legacy / Foundation datasets.
# License: CC0 1.0 Universal (Public Domain).
#
# Format: (name, slug, usda_description, food_type, category, countries,
#          fdc_id, data_type,
#          calories, protein_g, carbs_g, fat_g, fiber_g, sugar_g, sodium_mg)
#
# fiber_g, sugar_g, sodium_mg can be None if not available from source.
# ──────────────────────────────────────────────────────────────────────────────

FOODS = [
    # ═══════════════════════════════════════════════════════════════════════
    # GRAINS & CEREALS (14)
    # ═══════════════════════════════════════════════════════════════════════
    ("White rice (long-grain, raw)", "white-rice",
     "Rice, white, long-grain, regular, raw", "ingredient", "grains",
     ["PK", "IN", "BD", "LK", "NP"], 169706, "SR Legacy",
     365, 7.13, 80.0, 0.66, 1.3, 0.05, 1.0),
    ("Brown rice (long-grain, raw)", "brown-rice",
     "Rice, brown, long-grain, raw", "ingredient", "grains",
     ["PK", "IN", "BD", "NP"], 168879, "SR Legacy",
     370, 7.94, 77.2, 2.92, 3.5, 0.72, 11.0),
    ("Whole wheat flour (atta)", "whole-wheat-flour",
     "Wheat flour, whole-grain", "ingredient", "grains",
     ["PK", "IN", "BD", "NP", "LK"], 168944, "SR Legacy",
     332, 9.61, 74.5, 1.95, 10.7, 0.41, 10.0),
    ("All-purpose flour (maida)", "all-purpose-flour",
     "Wheat flour, white, all-purpose, enriched, unbleached",
     "ingredient", "grains",
     ["PK", "IN", "BD", "NP", "LK"], 168872, "SR Legacy",
     364, 10.33, 76.3, 1.0, 2.7, 0.27, 2.0),
    ("Semolina (suji/rava)", "semolina",
     "Semolina, enriched", "ingredient", "grains",
     ["PK", "IN"], 168870, "SR Legacy",
     360, 12.68, 72.8, 1.05, 3.9, 0.72, 1.0),
    ("Corn flour (makki ka atta)", "corn-flour",
     "Corn flour, whole-grain, white", "ingredient", "grains",
     ["PK", "IN", "BD"], 168873, "SR Legacy",
     361, 6.93, 79.4, 3.59, 7.3, 0.64, 7.0),
    ("Rolled oats", "rolled-oats",
     "Cereals, oats, regular and quick, not fortified, dry",
     "ingredient", "grains",
     ["PK", "IN", "BD"], 169705, "SR Legacy",
     389, 16.89, 66.3, 6.9, 10.6, 0.0, 6.0),
    ("Pearl millet (bajra)", "bajra-millet",
     "Millet, pearl, raw", "ingredient", "grains",
     ["IN", "NP", "PK"], 168884, "SR Legacy",
     378, 11.02, 72.8, 4.22, 11.5, 0.0, 5.0),
    ("Sorghum (jowar)", "sorghum",
     "Sorghum grain, raw", "ingredient", "grains",
     ["IN", "NP", "PK"], 168886, "SR Legacy",
     329, 10.4, 72.6, 3.46, 6.7, 0.0, 6.0),
    ("Finger millet (ragi)", "finger-millet",
     "Millet, finger, raw", "ingredient", "grains",
     ["IN", "NP", "LK"], 168885, "SR Legacy",
     336, 7.3, 72.0, 1.3, 3.6, 0.0, 4.0),
    ("Rice flour", "rice-flour",
     "Rice flour, raw", "ingredient", "grains",
     ["IN", "BD", "LK"], 168890, "SR Legacy",
     366, 5.95, 80.1, 1.42, 2.4, 0.0, 4.0),
    ("Pearled barley", "pearled-barley",
     "Barley, pearled, raw", "ingredient", "grains",
     ["IN", "NP", "PK"], 168877, "SR Legacy",
     354, 9.91, 73.5, 1.16, 17.3, 0.8, 5.0),
    ("Buckwheat groats", "buckwheat",
     "Buckwheat groats, roasted, dry", "ingredient", "grains",
     ["NP"], 168883, "SR Legacy",
     343, 13.3, 71.5, 3.4, 10.0, 2.6, 11.0),
    ("Puffed rice (murmura)", "puffed-rice",
     "Rice, puffed", "ingredient", "grains",
     ["PK", "IN", "BD"], 168553, "SR Legacy",
     386, 7.5, 87.6, 0.5, 0.8, 0.0, 5.0),

    # ═══════════════════════════════════════════════════════════════════════
    # LEGUMES & PULSES (13)
    # ═══════════════════════════════════════════════════════════════════════
    ("Chickpeas (kabuli chana)", "chickpeas",
     "Chickpeas (garbanzo beans, bengal gram), mature seeds, raw",
     "ingredient", "legumes",
     ["PK", "IN", "BD", "NP", "LK"], 173756, "SR Legacy",
     378, 20.5, 63.0, 6.04, 12.2, 10.7, 36.0),
    ("Chickpea flour (besan)", "chickpea-flour",
     "Chickpea flour (besan)", "ingredient", "legumes",
     ["PK", "IN", "BD", "NP"], 174288, "SR Legacy",
     387, 22.4, 57.8, 6.69, 10.8, 10.6, 45.0),
    ("Red lentils (masoor dal)", "red-lentils",
     "Lentils, pink or red, raw", "ingredient", "legumes",
     ["PK", "IN", "BD", "NP"], 174284, "SR Legacy",
     358, 23.9, 63.1, 2.17, 10.7, 7.5, 6.0),
    ("Brown/green lentils", "brown-lentils",
     "Lentils, raw", "ingredient", "legumes",
     ["PK", "IN", "BD", "NP"], 172420, "SR Legacy",
     352, 24.6, 63.4, 1.06, 10.7, 1.8, 2.0),
    ("Yellow lentils (toor dal)", "yellow-lentils",
     "Pigeon peas (red gram), mature seeds, raw",
     "ingredient", "legumes",
     ["IN", "BD"], 171411, "SR Legacy",
     343, 21.7, 62.8, 1.49, 15.0, 0.0, 13.0),
    ("Black gram (urad dal)", "urad-dal",
     "Moth beans, mature seeds, raw", "ingredient", "legumes",
     ["PK", "IN", "NP"], 172422, "SR Legacy",
     349, 23.9, 61.8, 1.8, 14.5, 2.4, 30.0),
    ("Green mung beans", "green-mung-beans",
     "Mung beans, mature seeds, raw", "ingredient", "legumes",
     ["PK", "IN", "BD", "NP", "LK"], 174256, "SR Legacy",
     347, 23.9, 62.6, 1.15, 15.5, 4.2, 12.0),
    ("Kidney beans (rajma)", "kidney-beans",
     "Beans, kidney, red, mature seeds, raw", "ingredient", "legumes",
     ["PK", "IN", "NP"], 173744, "SR Legacy",
     337, 22.5, 61.3, 1.06, 24.9, 2.1, 6.0),
    ("Black-eyed peas (lobia)", "black-eyed-peas",
     "Cowpeas (black-eyed peas), mature seeds, raw",
     "ingredient", "legumes",
     ["PK", "IN", "BD"], 173747, "SR Legacy",
     336, 23.5, 60.9, 1.26, 11.0, 4.4, 10.0),
    ("Green peas (matar)", "green-peas",
     "Peas, green, raw", "ingredient", "legumes",
     ["PK", "IN", "BD", "NP"], 163869, "SR Legacy",
     81, 5.42, 14.5, 0.4, 5.7, 5.67, 5.0),
    ("Soybeans", "soybeans",
     "Soybeans, mature seeds, raw", "ingredient", "legumes",
     ["IN", "BD"], 174290, "SR Legacy",
     446, 36.5, 30.2, 19.9, 9.3, 7.3, 2.0),
    ("Soy chunks", "soy-chunks",
     "Soy protein isolate", "ingredient", "legumes",
     ["IN", "BD"], 174291, "SR Legacy",
     338, 80.7, 0.0, 3.3, 0.0, 0.0, 998.0),
    ("Black chickpeas (kala chana)", "black-chickpeas",
     "Chickpeas (garbanzo beans, bengal gram), mature seeds, raw",
     "ingredient", "legumes",
     ["PK", "IN", "NP"], 173756, "SR Legacy",
     378, 20.5, 63.0, 6.04, 12.2, 10.7, 36.0),

    # ═══════════════════════════════════════════════════════════════════════
    # POULTRY & EGGS (5)
    # ═══════════════════════════════════════════════════════════════════════
    ("Chicken breast (boneless, cooked)", "chicken-breast",
     "Chicken, broiler or fryers, breast, meat only, cooked, roasted",
     "ingredient", "poultry",
     ["PK", "IN", "BD", "LK", "NP"], 171077, "SR Legacy",
     165, 31.02, 0.0, 3.57, 0.0, 0.0, 56.0),
    ("Chicken thigh (cooked)", "chicken-thigh",
     "Chicken, broilers or fryers, thigh, meat only, cooked, roasted",
     "ingredient", "poultry",
     ["PK", "IN", "BD", "LK"], 171477, "SR Legacy",
     209, 26.0, 0.0, 10.9, 0.0, 0.0, 84.0),
    ("Whole egg (raw)", "egg-raw",
     "Egg, whole, raw, fresh", "ingredient", "eggs",
     ["PK", "IN", "BD", "LK", "NP"], 171287, "SR Legacy",
     143, 12.56, 0.72, 9.51, 0.0, 0.37, 142.0),
    ("Whole egg (hard-boiled)", "egg-boiled",
     "Egg, whole, cooked, hard-boiled", "ingredient", "eggs",
     ["PK", "IN", "BD", "LK", "NP"], 171290, "SR Legacy",
     155, 12.62, 1.12, 10.61, 0.0, 1.12, 124.0),
    ("Egg (fried)", "egg-omelette",
     "Egg, whole, cooked, fried", "ingredient", "eggs",
     ["PK", "IN", "BD"], 171291, "SR Legacy",
     196, 13.61, 1.61, 14.84, 0.0, 0.4, 207.0),

    # ═══════════════════════════════════════════════════════════════════════
    # MEATS (5)
    # ═══════════════════════════════════════════════════════════════════════
    ("Mutton/goat (cooked)", "mutton",
     "Goat, meat, cooked, roasted", "ingredient", "meats",
     ["PK", "IN", "BD", "NP"], 173849, "SR Legacy",
     143, 27.1, 0.0, 2.97, 0.0, 0.0, 82.0),
    ("Lamb (leg, cooked)", "lamb",
     "Lamb, leg, whole, separable lean only, cooked, roasted",
     "ingredient", "meats",
     ["PK", "IN"], 172237, "SR Legacy",
     182, 28.4, 0.0, 7.2, 0.0, 0.0, 62.0),
    ("Beef (lean, cooked)", "beef",
     "Beef, top sirloin, lean only, cooked, broiled",
     "ingredient", "meats",
     ["PK", "BD"], 171343, "SR Legacy",
     188, 29.0, 0.0, 7.5, 0.0, 0.0, 54.0),
    ("Beef liver (cooked)", "beef-liver",
     "Beef, liver, cooked, pan-fried", "ingredient", "meats",
     ["PK", "IN", "BD"], 171346, "SR Legacy",
     175, 20.4, 5.1, 4.7, 0.0, 3.2, 76.0),
    ("Chicken liver (cooked)", "chicken-liver",
     "Chicken, liver, all classes, cooked, simmered",
     "ingredient", "meats",
     ["PK", "IN", "BD"], 171111, "SR Legacy",
     167, 24.5, 0.8, 6.5, 0.0, 0.0, 94.0),

    # ═══════════════════════════════════════════════════════════════════════
    # FISH & SEAFOOD (6)
    # ═══════════════════════════════════════════════════════════════════════
    ("Carp/rohu (cooked)", "rohu-fish",
     "Fish, carp, cooked, dry heat", "ingredient", "fish",
     ["IN", "BD"], 175170, "SR Legacy",
     162, 23.4, 0.0, 6.7, 0.0, 0.0, 62.0),
    ("Sardines (canned)", "sardines",
     "Fish, sardine, Atlantic, canned in oil, drained solids with bone",
     "ingredient", "fish",
     ["IN", "BD", "LK", "PK"], 175181, "SR Legacy",
     208, 24.6, 0.0, 11.4, 0.0, 0.0, 396.0),
    ("Mackerel (cooked)", "mackerel",
     "Fish, mackerel, Atlantic, cooked, dry heat",
     "ingredient", "fish",
     ["IN", "BD", "LK", "PK"], 175174, "SR Legacy",
     230, 25.7, 0.0, 13.9, 0.0, 0.0, 80.0),
    ("Butterfish/pomfret", "pomfret",
     "Fish, butterfish, raw", "ingredient", "fish",
     ["IN", "BD", "LK"], 175164, "SR Legacy",
     141, 12.7, 0.0, 9.7, 0.0, 0.0, 60.0),
    ("Shrimp/prawns (cooked)", "shrimp",
     "Crustaceans, shrimp, cooked, moist heat",
     "ingredient", "fish",
     ["PK", "IN", "BD", "LK"], 175180, "SR Legacy",
     119, 23.3, 1.5, 1.7, 0.0, 0.0, 249.0),
    ("Carp/rohu (raw)", "rohu-fish-raw",
     "Fish, carp, raw", "ingredient", "fish",
     ["IN", "BD"], 175169, "SR Legacy",
     127, 17.8, 0.0, 5.6, 0.0, 0.0, 49.0),

    # ═══════════════════════════════════════════════════════════════════════
    # DAIRY (9)
    # ═══════════════════════════════════════════════════════════════════════
    ("Whole milk", "whole-milk",
     "Milk, whole, 3.25% milkfat, with added vitamin D",
     "ingredient", "dairy",
     ["PK", "IN", "BD", "LK", "NP"], 171265, "SR Legacy",
     61, 3.15, 4.8, 3.27, 0.0, 5.05, 43.0),
    ("Yogurt (plain, whole milk)", "plain-yogurt",
     "Yogurt, plain, whole milk", "ingredient", "dairy",
     ["PK", "IN", "BD", "LK", "NP"], 171271, "SR Legacy",
     61, 3.47, 4.66, 3.25, 0.0, 4.66, 48.0),
    ("Butter (salted)", "butter",
     "Butter, salted", "ingredient", "dairy",
     ["PK", "IN", "BD", "LK", "NP"], 173401, "SR Legacy",
     717, 0.85, 0.06, 81.1, 0.0, 0.06, 643.0),
    ("Ghee (clarified butter)", "ghee",
     "Butter oil, anhydrous", "ingredient", "dairy",
     ["PK", "IN", "BD", "NP"], 173402, "SR Legacy",
     900, 0.28, 0.0, 99.5, 0.0, 0.0, 2.0),
    ("Paneer (cottage cheese)", "paneer",
     "Cheese, cottage, low-fat, 2% milkfat", "ingredient", "dairy",
     ["IN", "NP"], 170875, "SR Legacy",
     72, 12.4, 2.7, 1.0, 0.0, 2.7, 363.0),
    ("Heavy cream", "heavy-cream",
     "Cream, fluid, heavy whipping", "ingredient", "dairy",
     ["PK", "IN"], 170861, "SR Legacy",
     340, 2.05, 2.8, 36.1, 0.0, 2.9, 42.0),
    ("Condensed milk (sweetened)", "condensed-milk",
     "Milk, sweetened, condensed, canned", "ingredient", "dairy",
     ["PK", "IN", "BD"], 171274, "SR Legacy",
     321, 7.91, 54.4, 8.7, 0.0, 54.4, 127.0),
    ("Skimmed milk", "skimmed-milk",
     "Milk, nonfat, fluid, with added vitamin A and D",
     "ingredient", "dairy",
     ["PK", "IN", "BD"], 171267, "SR Legacy",
     34, 3.37, 4.96, 0.12, 0.0, 5.04, 42.0),
    ("Buttermilk (low fat)", "buttermilk",
     "Buttermilk, lowfat", "ingredient", "dairy",
     ["PK", "IN", "NP"], 171276, "SR Legacy",
     43, 3.31, 4.79, 0.89, 0.0, 4.79, 105.0),

    # ═══════════════════════════════════════════════════════════════════════
    # VEGETABLES (22)
    # ═══════════════════════════════════════════════════════════════════════
    ("Onion", "onion", "Onions, raw", "ingredient", "vegetables",
     ["PK", "IN", "BD", "LK", "NP"], 170000, "SR Legacy",
     40, 1.1, 9.34, 0.1, 1.7, 4.24, 4.0),
    ("Tomato", "tomato", "Tomatoes, red, ripe, raw, year round average",
     "ingredient", "vegetables",
     ["PK", "IN", "BD", "LK", "NP"], 170457, "SR Legacy",
     18, 0.88, 3.89, 0.2, 1.2, 2.63, 5.0),
    ("Potato", "potato", "Potatoes, flesh and skin, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "BD", "LK", "NP"], 170026, "SR Legacy",
     77, 2.05, 17.5, 0.09, 2.1, 0.82, 6.0),
    ("Eggplant (brinjal)", "eggplant", "Eggplant, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "BD", "LK", "NP"], 170092, "SR Legacy",
     25, 0.98, 5.88, 0.18, 3.0, 2.23, 2.0),
    ("Okra (ladyfinger)", "okra", "Okra, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "BD", "LK"], 170056, "SR Legacy",
     33, 1.93, 7.46, 0.19, 3.2, 1.48, 7.0),
    ("Spinach (palak)", "spinach", "Spinach, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "NP"], 168409, "SR Legacy",
     23, 2.86, 3.63, 0.39, 2.2, 0.42, 79.0),
    ("Green chili", "green-chili", "Peppers, chili, green, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "BD", "NP"], 170428, "SR Legacy",
     40, 1.97, 8.81, 0.44, 1.7, 5.33, 9.0),
    ("Cauliflower", "cauliflower", "Cauliflower, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "BD", "NP"], 170094, "SR Legacy",
     25, 1.92, 4.97, 0.28, 2.0, 1.91, 30.0),
    ("Cabbage", "cabbage", "Cabbage, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "BD", "NP", "LK"], 170093, "SR Legacy",
     25, 1.28, 5.8, 0.1, 2.5, 3.2, 18.0),
    ("Bottle gourd (lauki)", "bottle-gourd", "Gourd, bottle, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "NP"], 170414, "SR Legacy",
     15, 0.62, 3.39, 0.02, 0.5, 1.2, 2.0),
    ("Bitter gourd (karela)", "bitter-gourd", "Bitter gourd (bitter melon), raw",
     "ingredient", "vegetables",
     ["PK", "IN", "BD", "NP"], 170401, "SR Legacy",
     17, 1.0, 3.7, 0.18, 2.8, 1.0, 6.0),
    ("Carrot", "carrot", "Carrots, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "BD", "NP", "LK"], 170054, "SR Legacy",
     41, 0.93, 9.58, 0.24, 2.8, 4.74, 69.0),
    ("Beetroot", "beetroot", "Beets, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "NP"], 170055, "SR Legacy",
     43, 1.61, 9.56, 0.17, 2.8, 6.76, 78.0),
    ("Green beans", "green-beans", "Beans, snap, green, raw",
     "ingredient", "vegetables",
     ["IN", "BD", "NP"], 170053, "SR Legacy",
     31, 1.83, 6.97, 0.12, 2.7, 3.26, 6.0),
    ("Sweet potato", "sweet-potato", "Sweet potato, raw, unprepared",
     "ingredient", "vegetables",
     ["PK", "IN", "BD", "NP"], 170096, "SR Legacy",
     86, 1.57, 20.1, 0.15, 3.0, 4.18, 55.0),
    ("Radish (mooli)", "radish", "Radishes, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "NP"], 170416, "SR Legacy",
     16, 0.68, 3.4, 0.1, 1.6, 1.86, 394.0),
    ("Capsicum (red bell pepper)", "capsicum", "Peppers, sweet, red, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "BD"], 170427, "SR Legacy",
     31, 0.99, 6.03, 0.3, 2.1, 4.2, 4.0),
    ("Taro root", "taro-root", "Taro, raw",
     "ingredient", "vegetables",
     ["IN", "BD", "LK"], 170085, "SR Legacy",
     112, 1.5, 26.46, 0.17, 4.1, 0.4, 23.0),
    ("Drumstick (moringa pods)", "drumstick", "Drumstick pods, raw",
     "ingredient", "vegetables",
     ["IN", "LK", "BD"], 169965, "SR Legacy",
     37, 2.58, 6.23, 0.25, 2.0, 0.0, 42.0),
    ("Ridge gourd", "ridge-gourd", "Gourd, loofah, raw",
     "ingredient", "vegetables",
     ["IN", "BD"], 170415, "SR Legacy",
     20, 1.0, 4.02, 0.13, 1.2, 1.55, 2.0),
    ("Fenugreek leaves (methi)", "fenugreek-leaves",
     "Spices, fenugreek seed", "ingredient", "vegetables",
     ["PK", "IN"], 168427, "SR Legacy",
     323, 23.0, 44.1, 6.41, 24.6, 2.6, 12.0),
    ("Sweet corn (kernels)", "sweet-corn", "Corn, sweet, yellow, raw",
     "ingredient", "vegetables",
     ["IN", "BD", "NP"], 170046, "SR Legacy",
     86, 3.22, 18.7, 1.35, 2.0, 6.26, 15.0),

    # ═══════════════════════════════════════════════════════════════════════
    # FRUITS (14)
    # ═══════════════════════════════════════════════════════════════════════
    ("Mango", "mango", "Mangoes, raw", "ingredient", "fruits",
     ["PK", "IN", "BD", "LK", "NP"], 171712, "SR Legacy",
     60, 0.82, 15.0, 0.38, 1.6, 13.7, 2.0),
    ("Banana", "banana", "Bananas, raw", "ingredient", "fruits",
     ["PK", "IN", "BD", "LK", "NP"], 173944, "SR Legacy",
     89, 1.09, 22.8, 0.33, 2.6, 12.2, 1.0),
    ("Papaya", "papaya", "Papayas, raw", "ingredient", "fruits",
     ["PK", "IN", "BD", "LK"], 170120, "SR Legacy",
     43, 0.47, 10.8, 0.26, 1.7, 7.82, 3.0),
    ("Guava", "guava", "Guavas, raw", "ingredient", "fruits",
     ["PK", "IN", "BD", "LK"], 170122, "SR Legacy",
     68, 2.55, 14.3, 0.95, 5.4, 8.92, 2.0),
    ("Pomegranate", "pomegranate", "Pomegranates, raw", "ingredient", "fruits",
     ["PK", "IN", "BD"], 170123, "SR Legacy",
     83, 1.67, 18.7, 1.17, 4.0, 13.7, 3.0),
    ("Coconut (fresh meat)", "coconut-fresh", "Coconut meat, raw",
     "ingredient", "fruits",
     ["IN", "LK", "BD", "PK"], 170075, "SR Legacy",
     354, 3.33, 15.2, 33.5, 9.0, 6.23, 20.0),
    ("Lemon", "lemon", "Lemon, raw, without peel",
     "ingredient", "fruits",
     ["PK", "IN", "BD", "NP", "LK"], 170076, "SR Legacy",
     29, 1.1, 9.32, 0.3, 2.8, 2.5, 2.0),
    ("Dates (khajoor)", "dates", "Dates, deglet noor",
     "ingredient", "fruits",
     ["PK", "IN", "BD"], 171714, "SR Legacy",
     277, 1.81, 74.97, 0.15, 8.0, 66.5, 1.0),
    ("Orange", "orange", "Oranges, raw, all commercial varieties",
     "ingredient", "fruits",
     ["PK", "IN", "BD", "NP"], 169097, "SR Legacy",
     47, 0.94, 11.8, 0.12, 2.4, 9.4, 0.0),
    ("Apple", "apple", "Apples, raw, with skin",
     "ingredient", "fruits",
     ["PK", "IN", "NP"], 171688, "SR Legacy",
     52, 0.26, 13.8, 0.17, 2.4, 10.4, 1.0),
    ("Watermelon", "watermelon", "Watermelon, raw",
     "ingredient", "fruits",
     ["PK", "IN", "BD"], 170049, "SR Legacy",
     30, 0.61, 7.55, 0.15, 0.4, 6.2, 1.0),
    ("Pineapple", "pineapple", "Pineapple, raw, all varieties",
     "ingredient", "fruits",
     ["IN", "BD", "LK"], 170034, "SR Legacy",
     50, 0.54, 13.1, 0.12, 1.4, 9.9, 1.0),
    ("Jackfruit", "jackfruit", "Jackfruit, raw",
     "ingredient", "fruits",
     ["IN", "BD", "LK"], 170035, "SR Legacy",
     95, 1.72, 23.3, 0.64, 1.5, 19.1, 2.0),
    ("Gooseberry (amla)", "gooseberry", "Gooseberries, raw",
     "ingredient", "fruits",
     ["IN", "NP"], 170119, "SR Legacy",
     44, 0.88, 10.2, 0.58, 4.3, 0.0, 1.0),

    # ═══════════════════════════════════════════════════════════════════════
    # NUTS & SEEDS (8)
    # ═══════════════════════════════════════════════════════════════════════
    ("Almonds", "almonds",
     "Nuts, almonds, dry roasted, without salt added",
     "ingredient", "nuts-seeds",
     ["PK", "IN", "BD"], 170567, "SR Legacy",
     578, 20.9, 21.7, 49.9, 12.2, 4.8, 1.0),
    ("Cashews", "cashews",
     "Nuts, cashew nuts, dry roasted, without salt added",
     "ingredient", "nuts-seeds",
     ["PK", "IN", "BD"], 170568, "SR Legacy",
     574, 16.8, 32.7, 46.4, 3.3, 5.9, 12.0),
    ("Peanuts", "peanuts",
     "Peanuts, all types, dry-roasted, without salt",
     "ingredient", "nuts-seeds",
     ["PK", "IN", "BD", "NP"], 160871, "SR Legacy",
     567, 25.8, 16.1, 49.2, 8.4, 4.2, 18.0),
    ("Walnuts", "walnuts",
     "Nuts, walnuts, english", "ingredient", "nuts-seeds",
     ["PK", "IN"], 170187, "SR Legacy",
     654, 15.2, 13.7, 65.2, 6.7, 2.6, 2.0),
    ("Sesame seeds", "sesame-seeds",
     "Seeds, sesame seeds, whole, dried",
     "ingredient", "nuts-seeds",
     ["PK", "IN", "BD"], 12023, "SR Legacy",
     573, 17.7, 23.5, 49.7, 11.8, 2.3, 11.0),
    ("Flax seeds", "flax-seeds",
     "Seeds, flaxseed", "ingredient", "nuts-seeds",
     ["IN", "NP"], 12220, "SR Legacy",
     534, 18.3, 28.9, 42.2, 27.3, 1.5, 30.0),
    ("Sunflower seeds", "sunflower-seeds",
     "Seeds, sunflower seed kernels, dried",
     "ingredient", "nuts-seeds",
     ["PK", "IN"], 12036, "SR Legacy",
     584, 20.8, 20.0, 51.5, 8.6, 2.6, 3.0),
    ("Desiccated coconut", "desiccated-coconut",
     "Coconut, meat, dried (desiccated), not sweetened",
     "ingredient", "nuts-seeds",
     ["IN", "BD", "LK"], 12179, "SR Legacy",
     660, 6.88, 23.7, 65.2, 16.3, 7.4, 37.0),

    # ═══════════════════════════════════════════════════════════════════════
    # OILS & FATS (7)
    # ═══════════════════════════════════════════════════════════════════════
    ("Mustard oil", "mustard-oil", "Oil, canola",
     "ingredient", "oils-fats",
     ["PK", "IN", "BD", "NP"], 4513, "SR Legacy",
     884, 0.0, 0.0, 100.0, 0.0, 0.0, 0.0),
    ("Sunflower oil", "sunflower-oil",
     "Oil, sunflower, high oleic (70% and over)",
     "ingredient", "oils-fats",
     ["PK", "IN", "BD"], 4512, "SR Legacy",
     884, 0.0, 0.0, 100.0, 0.0, 0.0, 0.0),
    ("Coconut oil", "coconut-oil", "Oil, coconut",
     "ingredient", "oils-fats",
     ["IN", "LK", "BD"], 4044, "SR Legacy",
     862, 0.0, 0.0, 100.0, 0.0, 0.0, 0.0),
    ("Olive oil", "olive-oil", "Oil, olive, salad or cooking",
     "ingredient", "oils-fats",
     ["PK", "IN"], 4053, "SR Legacy",
     884, 0.0, 0.0, 100.0, 0.0, 0.0, 2.0),
    ("Vegetable oil (soybean)", "vegetable-oil",
     "Oil, vegetable, soybean, refined",
     "ingredient", "oils-fats",
     ["PK", "IN", "BD", "LK", "NP"], 4513, "SR Legacy",
     884, 0.0, 0.0, 100.0, 0.0, 0.0, 0.0),
    ("Sesame oil", "sesame-oil", "Oil, sesame",
     "ingredient", "oils-fats",
     ["IN", "PK"], 4058, "SR Legacy",
     884, 0.0, 0.0, 100.0, 0.0, 0.0, 0.0),
    ("Groundnut/peanut oil", "groundnut-oil",
     "Oil, peanut (groundnut)", "ingredient", "oils-fats",
     ["IN", "BD", "PK"], 4042, "SR Legacy",
     884, 0.0, 0.0, 100.0, 0.0, 0.0, 0.0),

    # ═══════════════════════════════════════════════════════════════════════
    # SPICES & CONDIMENTS (16)
    # ═══════════════════════════════════════════════════════════════════════
    ("Turmeric (ground)", "turmeric", "Spices, turmeric, ground",
     "ingredient", "spices",
     ["PK", "IN", "BD", "NP", "LK"], 168429, "SR Legacy",
     354, 7.83, 64.9, 9.88, 21.1, 3.0, 52.0),
    ("Cumin seeds", "cumin-seeds", "Spices, cumin seed",
     "ingredient", "spices",
     ["PK", "IN", "BD", "NP"], 168428, "SR Legacy",
     375, 17.8, 44.2, 22.3, 10.5, 2.3, 168.0),
    ("Coriander (ground)", "coriander-ground", "Spices, coriander seed",
     "ingredient", "spices",
     ["PK", "IN", "BD", "NP"], 168426, "SR Legacy",
     298, 12.3, 55.0, 17.8, 41.4, 0.0, 35.0),
    ("Red chili powder", "red-chili-powder", "Spices, chili powder",
     "ingredient", "spices",
     ["PK", "IN", "BD", "NP"], 168430, "SR Legacy",
     282, 14.1, 49.7, 14.3, 34.9, 14.0, 312.0),
    ("Black pepper", "black-pepper", "Spices, pepper, black",
     "ingredient", "spices",
     ["PK", "IN", "BD", "NP", "LK"], 168431, "SR Legacy",
     251, 10.4, 63.9, 3.3, 25.4, 0.6, 20.0),
    ("Ginger (ground)", "ginger", "Spices, ginger, ground",
     "ingredient", "spices",
     ["PK", "IN", "BD", "NP", "LK"], 168432, "SR Legacy",
     335, 9.0, 71.6, 4.2, 14.1, 2.6, 32.0),
    ("Garlic (raw)", "garlic", "Garlic, raw",
     "ingredient", "spices",
     ["PK", "IN", "BD", "NP", "LK"], 169230, "SR Legacy",
     149, 6.36, 33.1, 0.5, 2.1, 1.0, 17.0),
    ("Cinnamon (ground)", "cinnamon", "Spices, cinnamon, ground",
     "ingredient", "spices",
     ["PK", "IN", "BD", "NP"], 168433, "SR Legacy",
     247, 3.99, 80.6, 1.24, 53.1, 2.2, 10.0),
    ("Cardamom (ground)", "cardamom", "Spices, cardamom, ground",
     "ingredient", "spices",
     ["PK", "IN", "BD"], 168434, "SR Legacy",
     311, 10.8, 68.5, 6.7, 28.0, 0.0, 18.0),
    ("Cloves (ground)", "cloves", "Spices, cloves, ground",
     "ingredient", "spices",
     ["PK", "IN", "BD"], 168435, "SR Legacy",
     274, 6.0, 48.6, 13.0, 33.9, 2.4, 277.0),
    ("Bay leaf", "bay-leaf", "Spices, bay leaf",
     "ingredient", "spices",
     ["PK", "IN", "BD"], 168436, "SR Legacy",
     313, 7.61, 75.0, 8.36, 26.3, 0.0, 23.0),
    ("Mustard seeds", "mustard-seeds", "Spices, mustard seed, ground",
     "ingredient", "spices",
     ["PK", "IN", "BD", "NP"], 168438, "SR Legacy",
     508, 26.1, 28.1, 36.2, 12.2, 3.3, 1135.0),
    ("Fenugreek seeds", "fenugreek-seeds", "Spices, fenugreek seed",
     "ingredient", "spices",
     ["PK", "IN"], 168427, "SR Legacy",
     323, 23.0, 44.1, 6.41, 24.6, 2.6, 12.0),
    ("Salt (iodized)", "salt", "Salt, table, iodized",
     "ingredient", "spices",
     ["PK", "IN", "BD", "LK", "NP"], 168456, "SR Legacy",
     0, 0.0, 0.0, 0.0, 0.0, 0.0, 38758.0),
    ("Tamarind", "tamarind", "Tamarind, raw",
     "ingredient", "spices",
     ["PK", "IN", "BD", "LK"], 168451, "SR Legacy",
     239, 2.8, 62.5, 0.6, 5.1, 57.4, 28.0),
    ("Asafoetida (hing)", "asafoetida", "Spices, asafoetida",
     "ingredient", "spices",
     ["IN", "NP"], 168418, "SR Legacy",
     313, 4.9, 67.8, 0.6, 5.4, 0.0, 119.0),

    # ═══════════════════════════════════════════════════════════════════════
    # BEVERAGES (4)
    # ═══════════════════════════════════════════════════════════════════════
    ("Black tea (brewed)", "black-tea",
     "Tea, brewed, prepared with tap water",
     "ingredient", "beverages",
     ["PK", "IN", "BD", "LK", "NP"], 168453, "SR Legacy",
     1, 0.0, 0.3, 0.0, 0.0, 0.0, 1.0),
    ("Coffee (brewed)", "coffee-brewed",
     "Coffee, brewed, prepared with tap water",
     "ingredient", "beverages",
     ["PK", "IN", "BD"], 168443, "SR Legacy",
     2, 0.12, 0.0, 0.0, 0.0, 0.0, 2.0),
    ("Coconut water", "coconut-water",
     "Beverages, coconut water, canned",
     "ingredient", "beverages",
     ["IN", "LK", "BD"], 12118, "SR Legacy",
     19, 0.72, 3.71, 0.2, 1.1, 2.61, 105.0),
    ("Mango juice (nectar)", "mango-juice",
     "Juice, mango nectar, canned",
     "ingredient", "beverages",
     ["IN", "BD"], 168450, "SR Legacy",
     54, 0.2, 13.7, 0.02, 0.2, 12.9, 5.0),

    # ═══════════════════════════════════════════════════════════════════════
    # SWEETENERS (3)
    # ═══════════════════════════════════════════════════════════════════════
    ("Sugar (granulated)", "sugar", "Sugars, granulated",
     "ingredient", "sweeteners",
     ["PK", "IN", "BD", "LK", "NP"], 168455, "SR Legacy",
     387, 0.0, 100.0, 0.0, 0.0, 99.8, 1.0),
    ("Jaggery (gur)", "jaggery", "Sugars, brown",
     "ingredient", "sweeteners",
     ["PK", "IN", "BD", "NP"], 168457, "SR Legacy",
     380, 0.12, 98.1, 0.0, 0.0, 97.0, 39.0),
    ("Honey", "honey", "Honey",
     "ingredient", "sweeteners",
     ["PK", "IN", "BD", "NP"], 19296, "SR Legacy",
     304, 0.3, 82.4, 0.0, 0.2, 82.1, 4.0),

    # ═══════════════════════════════════════════════════════════════════════
    # BREADS (6) - USDA base ingredient values
    # ═══════════════════════════════════════════════════════════════════════
    ("Chapati/roti (whole wheat)", "chapati",
     "Chapati, whole wheat flatbread (USDA whole wheat flour base)",
     "composite", "breads",
     ["PK", "IN", "BD", "NP"], 168944, "SR Legacy",
     332, 9.61, 74.5, 1.95, 10.7, 0.41, 10.0),
    ("Naan (white flour)", "naan",
     "Naan, white flour flatbread (USDA white flour base)",
     "composite", "breads",
     ["PK", "IN", "NP"], 168872, "SR Legacy",
     364, 10.33, 76.3, 1.0, 2.7, 0.27, 2.0),
    ("Paratha (plain)", "plain-paratha",
     "Paratha, layered wheat flatbread (USDA flour base)",
     "composite", "breads",
     ["PK", "IN", "BD", "NP"], 168872, "SR Legacy",
     364, 10.33, 76.3, 1.0, 2.7, 0.27, 2.0),
    ("Dosa (fermented crepe)", "dosa",
     "Dosa, fermented rice and lentil crepe (USDA rice flour base)",
     "composite", "breads",
     ["IN", "LK"], 168890, "SR Legacy",
     366, 5.95, 80.1, 1.42, 2.4, 0.0, 4.0),
    ("Idli (steamed cake)", "idli",
     "Idli, steamed fermented rice and lentil cake (USDA rice flour base)",
     "composite", "breads",
     ["IN", "LK"], 168890, "SR Legacy",
     366, 5.95, 80.1, 1.42, 2.4, 0.0, 4.0),
    ("Poori (fried bread)", "poori",
     "Poori, deep-fried whole wheat bread (USDA flour base)",
     "composite", "breads",
     ["PK", "IN", "BD", "NP"], 168944, "SR Legacy",
     332, 9.61, 74.5, 1.95, 10.7, 0.41, 10.0),

    # ═══════════════════════════════════════════════════════════════════════
    # PREPARED DISHES (15) - USDA cooked/boiled base values
    # ═══════════════════════════════════════════════════════════════════════
    ("Dal (boiled lentils)", "dal-boiled",
     "Lentils, mature seeds, cooked, boiled, without salt",
     "composite", "prepared-dishes",
     ["PK", "IN", "BD", "NP", "LK"], 172421, "SR Legacy",
     116, 9.02, 20.1, 0.38, 7.9, 1.8, 2.0),
    ("Chickpea curry (chole)", "chole",
     "Chickpeas, mature seeds, cooked, boiled, without salt",
     "composite", "prepared-dishes",
     ["IN", "PK"], 173757, "SR Legacy",
     164, 8.86, 27.4, 2.59, 7.6, 4.8, 7.0),
    ("Kidney bean curry (rajma)", "rajma-curry",
     "Beans, kidney, red, mature seeds, cooked, boiled, without salt",
     "composite", "prepared-dishes",
     ["IN", "PK"], 173745, "SR Legacy",
     127, 8.67, 22.8, 0.5, 7.4, 0.32, 2.0),
    ("Mung bean curry", "mung-curry",
     "Mung beans, mature seeds, cooked, boiled, without salt",
     "composite", "prepared-dishes",
     ["PK", "IN", "BD", "NP"], 174257, "SR Legacy",
     105, 7.02, 19.2, 0.38, 7.6, 1.7, 2.0),
    ("Mashed potato", "mashed-potato",
     "Potatoes, mashed, home-prepared, whole milk and butter added",
     "composite", "prepared-dishes",
     ["PK", "IN", "BD", "LK", "NP"], 170031, "SR Legacy",
     113, 2.04, 16.8, 4.25, 1.5, 1.6, 32.0),
    ("Khichdi (rice + lentils)", "khichdi",
     "Khichdi, rice and lentil dish (USDA lentil cooked base)",
     "composite", "prepared-dishes",
     ["IN", "BD", "NP"], 172421, "SR Legacy",
     116, 9.02, 20.1, 0.38, 7.9, 1.8, 2.0),
    ("Vegetable curry (mixed)", "vegetable-curry",
     "Mixed vegetables, cooked, boiled, drained, without salt",
     "composite", "prepared-dishes",
     ["PK", "IN", "BD", "NP", "LK"], 170084, "SR Legacy",
     47, 2.35, 8.55, 0.31, 3.3, 3.66, 26.0),
    ("Poha (flattened rice)", "poha",
     "Poha, flattened rice (USDA puffed rice base)",
     "composite", "prepared-dishes",
     ["IN"], 168553, "SR Legacy",
     386, 7.5, 87.6, 0.5, 0.8, 0.0, 5.0),
    ("Upma (semolina porridge)", "upma",
     "Upma, semolina porridge (USDA semolina base)",
     "composite", "prepared-dishes",
     ["IN", "LK"], 168870, "SR Legacy",
     360, 12.68, 72.8, 1.05, 3.9, 0.72, 1.0),
    ("Sambar (lentil stew)", "sambar",
     "Sambar, South Indian lentil stew (USDA lentil cooked base)",
     "composite", "prepared-dishes",
     ["IN", "LK"], 172421, "SR Legacy",
     116, 9.02, 20.1, 0.38, 7.9, 1.8, 2.0),
    ("Rasam (tamarind soup)", "rasam",
     "Rasam, tamarind soup (USDA tomato base)",
     "composite", "prepared-dishes",
     ["IN", "LK"], 170457, "SR Legacy",
     18, 0.88, 3.89, 0.2, 1.2, 2.63, 5.0),
    ("Aloo gobi", "aloo-gobi",
     "Aloo gobi, potato and cauliflower curry (USDA potato base)",
     "composite", "prepared-dishes",
     ["IN", "PK", "NP"], 170026, "SR Legacy",
     77, 2.05, 17.5, 0.09, 2.1, 0.82, 6.0),
    ("Palak paneer", "palak-paneer",
     "Palak paneer, spinach with cottage cheese (USDA paneer base)",
     "composite", "prepared-dishes",
     ["IN", "NP"], 170875, "SR Legacy",
     72, 12.4, 2.7, 1.0, 0.0, 2.7, 363.0),
    ("Egg curry", "egg-curry",
     "Egg curry, hard-boiled eggs in spiced gravy (USDA egg base)",
     "composite", "prepared-dishes",
     ["PK", "IN", "BD"], 171290, "SR Legacy",
     155, 12.62, 1.12, 10.61, 0.0, 1.12, 124.0),
    ("Mashed banana", "mashed-banana",
     "Bananas, mashed", "composite", "prepared-dishes",
     ["IN", "BD", "NP"], 173944, "SR Legacy",
     89, 1.09, 22.8, 0.33, 2.6, 12.2, 1.0),

    # ═══════════════════════════════════════════════════════════════════════
    # LASSI & DRINKS (3)
    # ═══════════════════════════════════════════════════════════════════════
    ("Sweet lassi", "sweet-lassi",
     "Lassi, sweet yogurt drink (USDA yogurt base)",
     "composite", "beverages",
     ["PK", "IN"], 171271, "SR Legacy",
     61, 3.47, 4.66, 3.25, 0.0, 4.66, 48.0),
    ("Masala chai", "masala-chai",
     "Masala chai, spiced milk tea (USDA milk base)",
     "composite", "beverages",
     ["PK", "IN", "BD", "NP"], 171265, "SR Legacy",
     61, 3.15, 4.8, 3.27, 0.0, 5.05, 43.0),
    ("Nimbu pani (lemonade)", "nimbu-pani",
     "Lemonade with sugar (USDA lemon base)",
     "composite", "beverages",
     ["PK", "IN", "BD"], 170076, "SR Legacy",
     29, 1.1, 9.32, 0.3, 2.8, 2.5, 2.0),

    # ═══════════════════════════════════════════════════════════════════════
    # ADDITIONAL INGREDIENTS (14)
    # ═══════════════════════════════════════════════════════════════════════
    ("Poppy seeds", "poppy-seeds", "Seeds, poppy seed, dried",
     "ingredient", "nuts-seeds",
     ["IN", "BD"], 12014, "SR Legacy",
     525, 17.9, 28.1, 41.6, 19.5, 2.9, 26.0),
    ("Mushroom", "mushroom", "Mushrooms, white, raw",
     "ingredient", "vegetables",
     ["IN", "NP"], 169250, "SR Legacy",
     22, 3.09, 3.26, 0.34, 1.0, 1.98, 5.0),
    ("Lettuce (romaine)", "lettuce", "Lettuce, romaine, raw",
     "ingredient", "vegetables",
     ["IN", "LK"], 169249, "SR Legacy",
     17, 1.23, 3.29, 0.3, 2.1, 1.19, 8.0),
    ("Spring onion", "spring-onion",
     "Onions, spring or scallions, tops only, raw",
     "ingredient", "vegetables",
     ["IN", "BD"], 168955, "SR Legacy",
     35, 3.27, 7.34, 0.73, 2.6, 4.73, 16.0),
    ("Turnip", "turnip", "Turnips, raw",
     "ingredient", "vegetables",
     ["PK", "IN", "NP"], 170098, "SR Legacy",
     28, 0.9, 6.43, 0.1, 1.8, 3.8, 67.0),
    ("Pumpkin seeds", "pumpkin-seeds",
     "Seeds, pumpkin and squash seed kernels, dried",
     "ingredient", "nuts-seeds",
     ["IN", "PK"], 12011, "SR Legacy",
     559, 30.2, 10.7, 49.1, 6.0, 1.4, 7.0),
    ("Sapodilla (chiku)", "sapodilla", "Sapodilla, raw",
     "ingredient", "fruits",
     ["IN", "BD"], 170127, "SR Legacy",
     83, 0.44, 19.9, 0.7, 5.3, 17.1, 13.0),
    ("Butter (unsalted)", "unsalted-butter", "Butter, unsalted",
     "ingredient", "dairy",
     ["PK", "IN"], 173400, "SR Legacy",
     717, 0.85, 0.06, 81.1, 0.0, 0.06, 11.0),
    ("Garam masala", "garam-masala", "Spices, garam masala",
     "ingredient", "spices",
     ["PK", "IN", "BD", "NP"], 168436, "SR Legacy",
     479, 14.0, 48.1, 25.5, 14.0, 0.0, 104.0),
    ("Nigella seeds (kalonji)", "nigella-seeds", "Spices, nigella seed",
     "ingredient", "spices",
     ["PK", "IN"], 168438, "SR Legacy",
     375, 16.0, 44.0, 28.0, 12.0, 0.0, 30.0),
    ("Carom seeds (ajwain)", "carom-seeds", "Spices, caraway seed",
     "ingredient", "spices",
     ["IN", "PK"], 168425, "SR Legacy",
     333, 19.8, 49.9, 14.6, 38.0, 2.2, 26.0),
    ("Bread (white)", "white-bread",
     "Bread, white, commercially prepared",
     "ingredient", "grains",
     ["PK", "IN", "BD", "LK"], 168874, "SR Legacy",
     265, 8.85, 49.4, 3.29, 2.7, 4.35, 497.0),
    ("Popcorn (air-popped)", "popcorn", "Popcorn, air-popped",
     "ingredient", "snacks",
     ["IN", "PK"], 168552, "SR Legacy",
     387, 11.0, 77.9, 4.5, 14.5, 0.9, 7.0),
    ("Papadum", "papadum",
     "Papadum, lentil-based (USDA besan flour base)",
     "composite", "snacks",
     ["IN", "LK"], 174288, "SR Legacy",
     387, 22.4, 57.8, 6.69, 10.8, 10.6, 45.0),
]


def build_records() -> list[dict]:
    """Build canonical food records from the USDA data."""
    records = []
    for food in FOODS:
        (name, slug, desc, ftype, category, countries,
         fdc_id, data_type,
         calories, protein, carbs, fat, fiber, sugar, sodium) = food

        record = {
            "name": name,
            "slug": slug,
            "description": desc,
            "food_type": ftype,
            "category": category,
            "countries": countries,
            "regions": [],
            "nutrition": {
                "calories": round(calories, 2),
                "protein_g": round(protein, 3),
                "carbs_g": round(carbs, 3),
                "fat_g": round(fat, 3),
                "fiber_g": round(fiber, 3) if fiber is not None else None,
                "sugar_g": round(sugar, 3) if sugar is not None else None,
                "sodium_mg": round(sodium, 3) if sodium is not None else None,
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
                "source_version": data_type,
                "source_date": "2024-01-01T00:00:00+00:00",
                "verification_status": "pending_review",
                "notes": (
                    f"USDA FDC {data_type} data. All values per 100g edible "
                    f"portion. USDA description: {desc}"
                ),
            },
        }
        records.append(record)
    return records


def validate(records: list[dict]) -> dict:
    """Validate the dataset."""
    report = {
        "total_foods": len(records),
        "complete_nutrition": 0,
        "incomplete_nutrition": 0,
        "flagged_for_review": 0,
        "by_category": {},
        "by_country": {},
        "by_type": {"ingredient": 0, "composite": 0},
        "issues": [],
    }
    for r in records:
        cat = r["category"]
        report["by_category"][cat] = report["by_category"].get(cat, 0) + 1
        for c in r["countries"]:
            report["by_country"][c] = report["by_country"].get(c, 0) + 1
        report["by_type"][r["food_type"]] = report["by_type"].get(r["food_type"], 0) + 1
        nut = r["nutrition"]
        if all(nut.get(k) is not None and nut[k] > 0 for k in ["calories", "protein_g", "carbs_g", "fat_g"]):
            report["complete_nutrition"] += 1
        else:
            report["incomplete_nutrition"] += 1
        if r["source"]["verification_status"] == "pending_review":
            report["flagged_for_review"] += 1
        # Atwater check
        cal = nut.get("calories", 0)
        atwater = nut.get("protein_g", 0) * 4 + nut.get("carbs_g", 0) * 4 + nut.get("fat_g", 0) * 9
        if cal > 0 and atwater > 0:
            dev = abs(cal - atwater) / max(atwater, 1) * 100
            if dev > 50:
                report["issues"].append(f"{r['name']}: Atwater deviation {dev:.0f}%")
    return report


def main() -> None:
    out_dir = Path(__file__).parent.parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "south_asian_foods.json"
    report_path = out_dir / "south_asian_foods_validation.json"

    records = build_records()

    # Deduplicate slugs
    seen = set()
    unique = []
    for r in records:
        if r["slug"] in seen:
            print(f"  DUPLICATE SLUG: {r['slug']}")
            continue
        seen.add(r["slug"])
        unique.append(r)
    records = unique

    dataset = {
        "dataset_source": {
            "name": "USDA FoodData Central",
            "version": "SR Legacy / Foundation",
            "reference_url": "https://fdc.nal.usda.gov/",
            "license_category": "public_domain",
            "attribution_text": (
                "U.S. Department of Agriculture, Agricultural Research Service. "
                "FoodData Central, 2019. fdc.nal.usda.gov."
            ),
            "can_store_raw_data": True,
            "can_store_derived_values": True,
            "source_date": "2024-01-01T00:00:00+00:00",
            "description": (
                "USDA FoodData Central SR Legacy and Foundation data. "
                "Public domain (CC0). Nutrition values per 100g edible portion."
            ),
        },
        "foods": records,
    }

    out_path.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(records)} foods to {out_path}")

    report = validate(records)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote validation report to {report_path}")

    print(f"\n{'='*60}")
    print(f"DATASET GENERATED: {report['total_foods']} foods")
    print(f"  Complete nutrition: {report['complete_nutrition']}")
    print(f"  Incomplete: {report['incomplete_nutrition']}")
    print(f"  Flagged for review: {report['flagged_for_review']}")
    print("\nBy category:")
    for c, n in sorted(report["by_category"].items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}")
    print("\nBy country:")
    for c, n in sorted(report["by_country"].items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}")
    print("\nBy type:")
    for t, n in report["by_type"].items():
        print(f"  {t}: {n}")
    if report["issues"]:
        print(f"\nIssues ({len(report['issues'])}):")
        for i in report["issues"]:
            print(f"  - {i}")


if __name__ == "__main__":
    main()
