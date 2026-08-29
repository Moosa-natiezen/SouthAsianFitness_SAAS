FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY data ./data

EXPOSE ${PORT:-8000}

CMD uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
