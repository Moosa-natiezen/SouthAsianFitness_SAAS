from __future__ import annotations

import argparse
from pathlib import Path

from app.db.session import SessionLocal
from app.services.food_import_service import import_foods_from_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import a JSON food dataset into the application database.")
    parser.add_argument("dataset", help="Path to the JSON food dataset to import")
    parser.add_argument("--dry-run", action="store_true", help="Validate and summarize the import without committing changes")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    dataset_path = Path(args.dataset)

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    db = SessionLocal()
    try:
        summary = import_foods_from_file(db, dataset_path, dry_run=args.dry_run)
        mode = "dry-run" if args.dry_run else "import"
        print(f"Mode: {mode}")
        print(f"Imported: {summary.imported}")
        print(f"Updated: {summary.updated}")
        print(f"Skipped: {summary.skipped}")
        print(f"Failed: {summary.failed}")
        if summary.warnings:
            for warning in summary.warnings:
                print(f"Warning: {warning}")
    except (ValueError, OSError) as exc:  # pragma: no cover - CLI entrypoint
        print(f"Import failed: {exc}")
        return 1
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
