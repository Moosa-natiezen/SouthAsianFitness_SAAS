"""Shared pytest fixtures.

The AI response cache and cost metrics are process-wide singletons. Without
a per-test reset, cache state leaks across test modules (a test that
generates a plan makes later identical requests skip the mocked LLM). The
autouse fixture below guarantees every test starts with cold, isolated
cache/metric state.

NOTE: pytest imports conftest before any test module, so the standard test
env defaults must be set HERE (before the app imports below) — same pattern
as every test module uses.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

import pytest
from app.core.ai_cache import reset_ai_cache
from app.core.ai_metrics import ai_metrics


@pytest.fixture(autouse=True)
def _reset_ai_caches() -> None:
    """Reset AI cache + cost metrics before every test."""
    reset_ai_cache()
    ai_metrics.reset()
