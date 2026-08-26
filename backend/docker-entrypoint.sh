#!/bin/sh
set -e

echo "Running database migrations..."
uv run alembic upgrade head

echo "Seeding reference data (idempotent)..."
uv run python -m app.scripts.seed_reference_data

echo "Starting application server..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
