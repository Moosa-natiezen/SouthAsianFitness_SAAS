"""Tests for the health endpoints.

Covers:
- GET /health — root-level zero-I/O keep-alive probe ({"status": "ok"})
- GET /api/health — health check with DB diagnostics, always 200 + status "ok"
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from unittest.mock import patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_root_health_is_static_keepalive_payload() -> None:
    """GET /health returns the exact pinger contract with zero DB involvement."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_health_is_mounted_outside_api_prefix() -> None:
    """The keep-alive route lives at the root, not under /api."""
    openapi = client.get("/openapi.json").json() if client.get("/openapi.json").status_code == 200 else None
    if openapi is not None:  # docs are disabled in production configs
        assert "/health" in openapi["paths"]
        assert "/api/health" in openapi["paths"]


def test_api_health_deep_check_contract_intact() -> None:
    """GET /api/health keeps its diagnostic contract: DB + api + AI metrics fields."""
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["api"] == "ok"
    assert body["database"] == "connected"
    assert isinstance(body["ai_tokens_saved"], dict)


def test_api_health_stays_200_ok_while_database_is_down() -> None:
    """A cold/unreachable database must never turn the probe into a 503.

    Render restarts an instance whose health check fails, so a sleeping Neon
    compute has to surface as ``database: disconnected`` with HTTP 200.
    """
    with patch(
        "app.api.routes.health._db_probe_engine",
        side_effect=RuntimeError("db down"),
    ):
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "disconnected"


def test_health_endpoints_allow_vercel_origin_with_credentials() -> None:
    """CORS must serve the Vercel deployment origin for cookie-based auth."""
    for origin in (
        "https://southasianfitness.vercel.app",
        "https://southasianfitness.com",
        "https://www.southasianfitness.com",
    ):
        response = client.get("/health", headers={"Origin": origin})

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["access-control-allow-credentials"] == "true"
