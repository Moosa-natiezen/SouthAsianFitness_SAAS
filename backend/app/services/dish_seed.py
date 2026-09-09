"""Prepared South Asian dish catalog + idempotent seeding logic.

Single source of truth shared by:
  - scripts/seed_south_asian_foods.py (CLI)
  - app/api/routes/admin.py (GET /api/admin/seed-foods — for hosts without
    shell access, e.g. Render free tier)

Macros are per standard serving size.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import UnitDimension, VerificationStatus
from app.models.food import Food
from app.models.tags import CuisineTag, FoodCategory
from app.models.unit import Unit

# ── Prepared South Asian Dishes ─────────────────────────────────────────────

DISHES: list[dict] = [
    # ── Curries ──────────────────────────────────────────────────────────
    {
        "name": "Chicken Biryani",
        "slug": "chicken-biryani",
        "description": "Fragrant basmati rice layered with spiced chicken, saffron, and caramelized onions. A classic Hyderabadi-style biryani.",
        "serving_size": 350,
        "serving_unit_code": "g",
        "calories": 520,
        "protein_g": 32,
        "carbs_g": 58,
        "fat_g": 16,
        "fiber_g": 3,
        "sugar_g": 4,
        "sodium_mg": 680,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "indian", "hyderabadi"],
    },
    {
        "name": "Chicken Karahi",
        "slug": "chicken-karahi",
        "description": "Wok-fried chicken in a rich tomato and ginger gravy, a staple of Pakistani and North Indian cuisine.",
        "serving_size": 250,
        "serving_unit_code": "g",
        "calories": 380,
        "protein_g": 35,
        "carbs_g": 12,
        "fat_g": 22,
        "fiber_g": 2,
        "sugar_g": 6,
        "sodium_mg": 590,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "north-indian"],
    },
    {
        "name": "Paneer Tikka Masala",
        "slug": "paneer-tikka-masala",
        "description": "Chargrilled paneer cubes in a creamy, spiced tomato gravy. Rich in protein and vegetarian-friendly.",
        "serving_size": 250,
        "serving_unit_code": "g",
        "calories": 420,
        "protein_g": 22,
        "carbs_g": 18,
        "fat_g": 30,
        "fiber_g": 2,
        "sugar_g": 8,
        "sodium_mg": 520,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["indian", "punjabi"],
    },
    {
        "name": "Butter Chicken (Murgh Makhani)",
        "slug": "butter-chicken",
        "description": "Tender chicken pieces in a velvety tomato-butter cream sauce. A globally beloved North Indian classic.",
        "serving_size": 250,
        "serving_unit_code": "g",
        "calories": 450,
        "protein_g": 30,
        "carbs_g": 14,
        "fat_g": 32,
        "fiber_g": 1,
        "sugar_g": 7,
        "sodium_mg": 620,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["indian", "punjabi"],
    },
    {
        "name": "Palak Paneer",
        "slug": "palak-paneer",
        "description": "Cottage cheese cubes simmered in a spiced spinach purée. A protein-rich vegetarian staple.",
        "serving_size": 250,
        "serving_unit_code": "g",
        "calories": 310,
        "protein_g": 18,
        "carbs_g": 12,
        "fat_g": 22,
        "fiber_g": 4,
        "sugar_g": 3,
        "sodium_mg": 480,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["indian", "punjabi"],
    },
    {
        "name": "Daal Chawal (Lentils with Rice)",
        "slug": "daal-chawal",
        "description": "Slow-cooked yellow lentil curry served over steamed basmati rice. A comforting protein-packed staple across South Asia.",
        "serving_size": 400,
        "serving_unit_code": "g",
        "calories": 420,
        "protein_g": 20,
        "carbs_g": 65,
        "fat_g": 6,
        "fiber_g": 8,
        "sugar_g": 3,
        "sodium_mg": 450,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "indian"],
    },
    {
        "name": "Chicken Korma",
        "slug": "chicken-korma",
        "description": "Mild, creamy curry with tender chicken in a yogurt and cashew-based sauce with warm spices.",
        "serving_size": 250,
        "serving_unit_code": "g",
        "calories": 400,
        "protein_g": 28,
        "carbs_g": 10,
        "fat_g": 28,
        "fiber_g": 1,
        "sugar_g": 4,
        "sodium_mg": 540,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "mughlai"],
    },
    # ── Breads & Rice ────────────────────────────────────────────────────
    {
        "name": "Garlic Naan",
        "slug": "garlic-naan",
        "description": "Soft leavened bread brushed with garlic butter and baked in a tandoor. A perfect pairing for curries.",
        "serving_size": 1,
        "serving_unit_code": "roti",
        "calories": 260,
        "protein_g": 7,
        "carbs_g": 40,
        "fat_g": 8,
        "fiber_g": 2,
        "sugar_g": 3,
        "sodium_mg": 420,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["indian", "punjabi"],
    },
    {
        "name": "Jeera Rice (Cumin Rice)",
        "slug": "jeera-rice",
        "description": "Fragrant basmati rice tempered with cumin seeds and ghee. A simple yet aromatic side dish.",
        "serving_size": 200,
        "serving_unit_code": "g",
        "calories": 280,
        "protein_g": 5,
        "carbs_g": 52,
        "fat_g": 6,
        "fiber_g": 1,
        "sugar_g": 0,
        "sodium_mg": 180,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["indian"],
    },
    # ── Street Food ──────────────────────────────────────────────────────
    {
        "name": "Chicken Samosa (2 pieces)",
        "slug": "chicken-samosa",
        "description": "Crispy deep-fried pastry parcels filled with spiced minced chicken, peas, and herbs.",
        "serving_size": 2,
        "serving_unit_code": "katori",
        "calories": 340,
        "protein_g": 14,
        "carbs_g": 32,
        "fat_g": 18,
        "fiber_g": 2,
        "sugar_g": 2,
        "sodium_mg": 480,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "indian", "street-food"],
    },
    {
        "name": "Chicken Seekh Kebab (2 pieces)",
        "slug": "chicken-seekh-kebab",
        "description": "Minced chicken skewers seasoned with green chili, ginger, and fresh herbs, grilled over charcoal.",
        "serving_size": 120,
        "serving_unit_code": "g",
        "calories": 210,
        "protein_g": 24,
        "carbs_g": 4,
        "fat_g": 11,
        "fiber_g": 0,
        "sugar_g": 1,
        "sodium_mg": 380,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "mughlai"],
    },
    {
        "name": "Aloo Tikki (2 pieces)",
        "slug": "aloo-tikki",
        "description": "Crispy pan-fried spiced potato patties, a beloved Indian street food often served with chutneys.",
        "serving_size": 2,
        "serving_unit_code": "katori",
        "calories": 250,
        "protein_g": 4,
        "carbs_g": 38,
        "fat_g": 10,
        "fiber_g": 3,
        "sugar_g": 2,
        "sodium_mg": 350,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["indian", "street-food"],
    },
    # ── Sweets ───────────────────────────────────────────────────────────
    {
        "name": "Gulab Jamun (2 pieces)",
        "slug": "gulab-jamun",
        "description": "Soft milk-solid dumplings deep-fried and soaked in rose-cardamom sugar syrup. A festive South Asian dessert.",
        "serving_size": 2,
        "serving_unit_code": "katori",
        "calories": 300,
        "protein_g": 4,
        "carbs_g": 52,
        "fat_g": 10,
        "fiber_g": 0,
        "sugar_g": 42,
        "sodium_mg": 120,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "indian"],
    },
    {
        "name": "Kheer (Rice Pudding)",
        "slug": "kheer",
        "description": "Creamy slow-cooked rice pudding with milk, sugar, cardamom, and topped with pistachios and almonds.",
        "serving_size": 200,
        "serving_unit_code": "g",
        "calories": 220,
        "protein_g": 6,
        "carbs_g": 36,
        "fat_g": 7,
        "fiber_g": 1,
        "sugar_g": 28,
        "sodium_mg": 100,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "indian"],
    },
    {
        "name": "Chicken Haleem",
        "slug": "chicken-haleem",
        "description": "Rich, slow-cooked stew of shredded chicken, wheat, lentils, and spices. A hearty Hyderabadi classic.",
        "serving_size": 300,
        "serving_unit_code": "g",
        "calories": 440,
        "protein_g": 30,
        "carbs_g": 42,
        "fat_g": 16,
        "fiber_g": 6,
        "sugar_g": 3,
        "sodium_mg": 620,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["hyderabadi", "pakistani"],
    },
    # ── Breakfast ───────────────────────────────────────────────────────
    {
        "name": "Anda Paratha",
        "slug": "anda-paratha",
        "description": "Whole wheat paratha stuffed with spiced scrambled eggs, a hearty Pakistani breakfast.",
        "serving_size": 250,
        "serving_unit_code": "g",
        "calories": 380,
        "protein_g": 16,
        "carbs_g": 38,
        "fat_g": 18,
        "fiber_g": 3,
        "sugar_g": 2,
        "sodium_mg": 420,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "north-indian"],
    },
    {
        "name": "Aloo Paratha",
        "slug": "aloo-paratha",
        "description": "Crispy whole wheat flatbread stuffed with spiced mashed potatoes, served with yogurt and pickles.",
        "serving_size": 280,
        "serving_unit_code": "g",
        "calories": 400,
        "protein_g": 8,
        "carbs_g": 52,
        "fat_g": 18,
        "fiber_g": 4,
        "sugar_g": 3,
        "sodium_mg": 380,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["punjabi", "north-indian"],
    },
    {
        "name": "Anda Bhurji with Roti",
        "slug": "anda-bhurji-roti",
        "description": "Spiced Indian-style scrambled eggs with onions, tomatoes, and green chilies, served with whole wheat roti.",
        "serving_size": 300,
        "serving_unit_code": "g",
        "calories": 350,
        "protein_g": 20,
        "carbs_g": 30,
        "fat_g": 17,
        "fiber_g": 3,
        "sugar_g": 3,
        "sodium_mg": 410,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["indian", "punjabi"],
    },
    {
        "name": "Masala Oats",
        "slug": "masala-oats",
        "description": "Savory Indian-style oats cooked with onions, tomatoes, green chilies, and aromatic spices.",
        "serving_size": 300,
        "serving_unit_code": "g",
        "calories": 250,
        "protein_g": 10,
        "carbs_g": 38,
        "fat_g": 6,
        "fiber_g": 5,
        "sugar_g": 2,
        "sodium_mg": 350,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["indian"],
    },
    {
        "name": "Nihari (Fit Portion)",
        "slug": "nihari-fit",
        "description": "Slow-cooked bone-in beef stew with a rich, spiced gravy. A legendary Hyderabadi/Pakistani breakfast dish (leaner portion).",
        "serving_size": 250,
        "serving_unit_code": "g",
        "calories": 380,
        "protein_g": 32,
        "carbs_g": 8,
        "fat_g": 24,
        "fiber_g": 1,
        "sugar_g": 2,
        "sodium_mg": 580,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "hyderabadi"],
    },
    # ── Lunch / Light Meals ─────────────────────────────────────────────
    {
        "name": "Khichdi",
        "slug": "khichdi",
        "description": "Comfort food of rice and lentils cooked together with turmeric and cumin, served with ghee and pickles.",
        "serving_size": 350,
        "serving_unit_code": "g",
        "calories": 350,
        "protein_g": 14,
        "carbs_g": 55,
        "fat_g": 8,
        "fiber_g": 6,
        "sugar_g": 2,
        "sodium_mg": 380,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "indian"],
    },
    {
        "name": "Shami Kebab with Roti",
        "slug": "shami-kebab-roti",
        "description": "Pan-fried minced meat patties with chickpeas and spices, served with whole wheat roti.",
        "serving_size": 300,
        "serving_unit_code": "g",
        "calories": 420,
        "protein_g": 28,
        "carbs_g": 35,
        "fat_g": 18,
        "fiber_g": 4,
        "sugar_g": 2,
        "sodium_mg": 480,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "mughlai"],
    },
    {
        "name": "Fruit Chaat with Greek Yogurt",
        "slug": "fruit-chaat-yogurt",
        "description": "Fresh seasonal fruits tossed with chaat masala and served with a side of Greek yogurt.",
        "serving_size": 300,
        "serving_unit_code": "g",
        "calories": 220,
        "protein_g": 10,
        "carbs_g": 38,
        "fat_g": 4,
        "fiber_g": 4,
        "sugar_g": 28,
        "sodium_mg": 120,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "indian", "street-food"],
    },
    {
        "name": "Chicken Salan with Chapati",
        "slug": "chicken-salan-chapati",
        "description": "Spiced chicken curry in a rich onion-tomato gravy, served with whole wheat chapati.",
        "serving_size": 400,
        "serving_unit_code": "g",
        "calories": 480,
        "protein_g": 30,
        "carbs_g": 42,
        "fat_g": 20,
        "fiber_g": 5,
        "sugar_g": 4,
        "sodium_mg": 560,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "punjabi"],
    },
    # ── Dinner ──────────────────────────────────────────────────────────
    {
        "name": "Chicken Pulao",
        "slug": "chicken-pulao",
        "description": "Fragrant basmati rice cooked with tender chicken pieces, whole garam masala, and aromatic spices.",
        "serving_size": 350,
        "serving_unit_code": "g",
        "calories": 460,
        "protein_g": 28,
        "carbs_g": 55,
        "fat_g": 14,
        "fiber_g": 2,
        "sugar_g": 2,
        "sodium_mg": 520,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "hyderabadi"],
    },
    {
        "name": "Aloo Keema",
        "slug": "aloo-keema",
        "description": "Spiced minced meat cooked with diced potatoes, a classic Pakistani comfort dish.",
        "serving_size": 300,
        "serving_unit_code": "g",
        "calories": 380,
        "protein_g": 25,
        "carbs_g": 22,
        "fat_g": 22,
        "fiber_g": 3,
        "sugar_g": 3,
        "sodium_mg": 490,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "punjabi"],
    },
    {
        "name": "Karela Keema",
        "slug": "karela-keema",
        "description": "Bitter gourd stir-fried with spiced minced meat, onions, and tomatoes. A Pakistani home-style dish.",
        "serving_size": 250,
        "serving_unit_code": "g",
        "calories": 320,
        "protein_g": 22,
        "carbs_g": 15,
        "fat_g": 20,
        "fiber_g": 4,
        "sugar_g": 4,
        "sodium_mg": 440,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani"],
    },
    {
        "name": "Spiced Grilled Fish",
        "slug": "spiced-grilled-fish",
        "description": "Fish fillets marinated in a blend of South Asian spices, lemon, and herbs, then grilled to perfection.",
        "serving_size": 200,
        "serving_unit_code": "g",
        "calories": 260,
        "protein_g": 34,
        "carbs_g": 4,
        "fat_g": 12,
        "fiber_g": 1,
        "sugar_g": 1,
        "sodium_mg": 380,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "coastal"],
    },
    {
        "name": "Palak Paneer with Roti",
        "slug": "palak-paneer-roti",
        "description": "Cottage cheese cubes in a spiced spinach purée, served with whole wheat roti for a complete meal.",
        "serving_size": 350,
        "serving_unit_code": "g",
        "calories": 420,
        "protein_g": 22,
        "carbs_g": 38,
        "fat_g": 22,
        "fiber_g": 6,
        "sugar_g": 3,
        "sodium_mg": 480,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["punjabi", "north-indian"],
    },
    {
        "name": "Karahi Chicken with Naan",
        "slug": "karahi-chicken-naan",
        "description": "Wok-fried chicken in a rich tomato-ginger gravy, served with fluffy garlic naan.",
        "serving_size": 350,
        "serving_unit_code": "g",
        "calories": 520,
        "protein_g": 35,
        "carbs_g": 45,
        "fat_g": 24,
        "fiber_g": 3,
        "sugar_g": 5,
        "sodium_mg": 620,
        "category_slug": "prepared-dishes",
        "cuisine_tags": ["pakistani", "north-indian"],
    },
]


def seed_prepared_dishes(db: Session) -> tuple[int, int]:
    """Seed the prepared dish catalog. Idempotent — skips existing slugs.

    Self-sufficient: creates the ``prepared-dishes`` category and the gram
    unit if missing, so it works on any database (including fresh ones).

    Returns ``(created, skipped)`` counts. Commits on success; rolls back
    and re-raises on failure.
    """
    category = (
        db.query(FoodCategory).filter(FoodCategory.slug == "prepared-dishes").first()
    )
    if category is None:
        category = FoodCategory(name="Prepared Dishes", slug="prepared-dishes")
        db.add(category)
        db.flush()

    gram_unit = db.query(Unit).filter(Unit.code == "g").first()
    if gram_unit is None:
        gram_unit = Unit(
            code="g", name="gram", dimension=UnitDimension.MASS, to_base_factor=1
        )
        db.add(gram_unit)
        db.flush()

    cuisine_tag_cache: dict[str, CuisineTag] = {}
    created = 0
    skipped = 0

    try:
        for dish in DISHES:
            existing = db.query(Food).filter(Food.slug == dish["slug"]).first()
            if existing:
                skipped += 1
                continue

            unit_code = dish["serving_unit_code"]
            if unit_code == "g":
                unit = gram_unit
            else:
                unit = db.query(Unit).filter(Unit.code == unit_code).first()
                if unit is None:
                    # Fall back to grams; the optimizer treats a missing
                    # grams_per_serving as a 100 g reference portion.
                    unit = gram_unit

            food = Food(
                slug=dish["slug"],
                name=dish["name"],
                description=dish["description"],
                category_id=category.id,
                serving_size=dish["serving_size"],
                serving_unit_id=unit.id,
                grams_per_serving=(
                    dish["serving_size"] if unit_code == "g" else None
                ),
                calories=dish["calories"],
                protein_g=dish["protein_g"],
                carbs_g=dish["carbs_g"],
                fat_g=dish["fat_g"],
                fiber_g=dish.get("fiber_g"),
                sugar_g=dish.get("sugar_g"),
                sodium_mg=dish.get("sodium_mg"),
                is_active=True,
                verification_status=VerificationStatus.VERIFIED,
            )
            db.add(food)
            db.flush()

            for tag_slug in dish.get("cuisine_tags", []):
                if tag_slug not in cuisine_tag_cache:
                    tag = (
                        db.query(CuisineTag)
                        .filter(CuisineTag.slug == tag_slug)
                        .first()
                    )
                    if tag is None:
                        tag = CuisineTag(
                            slug=tag_slug,
                            name=tag_slug.replace("-", " ").title(),
                        )
                        db.add(tag)
                        db.flush()
                    cuisine_tag_cache[tag_slug] = tag
                food.cuisine_tags.append(cuisine_tag_cache[tag_slug])

            created += 1

        db.commit()
    except Exception:
        db.rollback()
        raise

    return created, skipped
