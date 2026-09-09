"""Seed the database with prepared South Asian dishes.

Run: cd backend && python scripts/seed_south_asian_foods.py

The dish catalog and seeding logic live in app/services/dish_seed.py so the
same data can also be seeded via GET /api/admin/seed-foods (for hosts
without shell access, e.g. Render free tier).
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Ensure the app package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.services.dish_seed import seed_prepared_dishes


def main() -> None:
    print("Seeding South Asian prepared dishes...")
    db = SessionLocal()
    try:
        created, skipped = seed_prepared_dishes(db)
    except Exception:
        db.close()
        raise
    db.close()
    print(f"\nDone! Created: {created}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
