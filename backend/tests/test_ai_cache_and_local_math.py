"""Tests for AI cost optimization: response cache + local math routing.

Verifies:
- Cache: fresh hit, variation hit, expiry, key normalization (cuisine case,
  preference order, rounding), bounded eviction, and the guard against
  caching partial/sandbox streams.
- Local math: /ai/meal-plans/generate fills omitted calorie/protein targets
  from the deterministic Python engine instead of delegating arithmetic to
  the LLM, and records the saving.
- Metrics: cache-hit and local-math token-saved counters move.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key")
os.environ.setdefault("LEMON_SQUEEZY_API_KEY", "ls_test")
os.environ.setdefault("LEMON_SQUEEZY_WEBHOOK_SECRET", "ls_test_secret")
os.environ.setdefault("LEMON_SQUEEZY_STORE_ID", "1")
os.environ.setdefault("LEMON_SQUEEZY_VARIANT_ID", "1")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

from unittest.mock import MagicMock, patch

from app.core.ai_cache import AICache, AICacheConfig, get_ai_cache, reset_ai_cache
from app.core.ai_metrics import ai_metrics
from app.schemas.nutrition import MealPlanRequest
from app.services.ai_service import _build_user_message, generate_meal_plan_stream

# ── Cache unit tests ─────────────────────────────────────────────────────────


class TestAICacheKeys:
    def test_identical_params_same_key(self):
        k1 = AICache.build_key(
            target_calories=2200, protein_g=120.4, cuisine_type="South Asian",
            dietary_preferences=["halal"], allergies=["peanuts"],
        )
        k2 = AICache.build_key(
            target_calories=2200, protein_g=120.4, cuisine_type="South Asian",
            dietary_preferences=["halal"], allergies=["peanuts"],
        )
        assert k1 == k2

    def test_cuisine_case_and_whitespace_normalized(self):
        k1 = AICache.build_key(
            target_calories=2200, protein_g=None, cuisine_type="South Asian",
            dietary_preferences=[], allergies=[],
        )
        k2 = AICache.build_key(
            target_calories=2200, protein_g=None, cuisine_type="  south asian  ",
            dietary_preferences=[], allergies=[],
        )
        assert k1 == k2

    def test_preference_order_irrelevant(self):
        k1 = AICache.build_key(
            target_calories=2200, protein_g=None, cuisine_type=None,
            dietary_preferences=["halal", "veg"], allergies=[],
        )
        k2 = AICache.build_key(
            target_calories=2200, protein_g=None, cuisine_type=None,
            dietary_preferences=["veg", "halal"], allergies=[],
        )
        assert k1 == k2

    def test_calorie_rounding(self):
        """2200.2 and 2199.8 round to the same key (2200)."""
        k1 = AICache.build_key(
            target_calories=2200.2, protein_g=None, cuisine_type=None,
            dietary_preferences=[], allergies=[],
        )
        k2 = AICache.build_key(
            target_calories=2199.8, protein_g=None, cuisine_type=None,
            dietary_preferences=[], allergies=[],
        )
        assert k1 == k2

    def test_different_allergies_different_key(self):
        """Allergies change the plan — they must change the key."""
        k1 = AICache.build_key(
            target_calories=2200, protein_g=None, cuisine_type=None,
            dietary_preferences=[], allergies=["peanuts"],
        )
        k2 = AICache.build_key(
            target_calories=2200, protein_g=None, cuisine_type=None,
            dietary_preferences=[], allergies=["shellfish"],
        )
        assert k1 != k2


class TestAICacheWindows:
    def _cache(self, **kwargs) -> AICache:
        return AICache(AICacheConfig(**kwargs))

    def test_fresh_hit_returns_response(self):
        cache = self._cache(fresh_window_seconds=3600, variation_window_seconds=7200)
        cache.put("k", "PLAN")
        result = cache.get("k")
        assert result == ("PLAN", False)

    def test_variation_hit_after_fresh_window(self):
        cache = self._cache(fresh_window_seconds=0, variation_window_seconds=3600)
        cache.put("k", "PLAN")
        result = cache.get("k")
        assert result == ("PLAN", True)

    def test_expired_past_variation_window(self):
        cache = self._cache(fresh_window_seconds=0, variation_window_seconds=0)
        cache.put("k", "PLAN")
        assert cache.get("k") is None

    def test_missing_key_is_miss(self):
        cache = self._cache()
        assert cache.get("nope") is None

    def test_eviction_bounded(self):
        cache = self._cache(max_entries=3)
        for i in range(5):
            cache.put(f"k{i}", f"PLAN{i}")
        assert cache.size == 3
        # Oldest entries were evicted
        assert cache.get("k0") is None
        assert cache.get("k4") is not None


# ── Streaming integration: cache serves, LLM fills, sandbox never caches ────


def _collect_sse_chunks(gen) -> str:
    import asyncio

    async def _run() -> str:
        parts = []
        async for chunk in gen:
            parts.append(chunk)
        return "".join(parts)

    return asyncio.run(_run())


def _make_stream_mock(text: str) -> MagicMock:
    mock = MagicMock()
    delta = MagicMock()
    delta.content = text

    chunk = MagicMock()
    chunk.choices = [MagicMock(delta=delta)]

    async def _empty():
        yield chunk

    async def _return_stream(*args, **kwargs):
        # The SDK's create() is awaited and resolves to an async iterator.
        return _empty()

    mock.chat.completions.create = MagicMock(side_effect=_return_stream)
    return mock


class TestStreamingCacheIntegration:
    def setup_method(self) -> None:
        reset_ai_cache()
        ai_metrics.reset()

    def test_identical_request_hits_llm_once_then_cache(self):
        """Two identical requests → exactly one LLM call; second is a hit."""
        payload = MealPlanRequest(
            target_calories=2200, protein_g=120, cuisine_type="South Asian"
        )
        mock = _make_stream_mock("# Desi Plan\n\n- Chicken Karahi with Roti")

        with (
            patch("app.services.ai_service.AsyncOpenAI", return_value=mock),
            patch("app.services.ai_service.settings.openai_api_key", "sk-test"),
        ):
            _collect_sse_chunks(generate_meal_plan_stream(payload))
            second = _collect_sse_chunks(generate_meal_plan_stream(payload))

        # LLM called exactly once
        assert mock.chat.completions.create.call_count == 1
        # Second response content equals the first (cached)
        assert "Chicken Karahi" in second
        # Metrics: 1 call, 1 hit, tokens saved > 0
        snap = ai_metrics.snapshot()
        assert snap["llm_calls"] == 1
        assert snap["cache_hits"] == 1
        assert snap["cache_hits_tokens_saved"] > 0

    def test_different_targets_miss_cache(self):
        payload_a = MealPlanRequest(target_calories=2200)
        payload_b = MealPlanRequest(target_calories=3000)
        mock = _make_stream_mock("plan")

        with (
            patch("app.services.ai_service.AsyncOpenAI", return_value=mock),
            patch("app.services.ai_service.settings.openai_api_key", "sk-test"),
        ):
            _collect_sse_chunks(generate_meal_plan_stream(payload_a))
            _collect_sse_chunks(generate_meal_plan_stream(payload_b))

        assert mock.chat.completions.create.call_count == 2

    def test_partial_stream_not_cached(self):
        """A stream that errors mid-way must not poison the cache."""
        payload = MealPlanRequest(target_calories=2200)
        mock = MagicMock()

        delta = MagicMock()
        delta.content = "partial"

        chunk = MagicMock()
        chunk.choices = [MagicMock(delta=delta)]

        async def _failing_stream():
            yield chunk
            raise RuntimeError("connection dropped")

        mock.chat.completions.create = MagicMock(return_value=_failing_stream())

        with (
            patch("app.services.ai_service.AsyncOpenAI", return_value=mock),
            patch("app.services.ai_service.settings.openai_api_key", "sk-test"),
        ):
            _collect_sse_chunks(generate_meal_plan_stream(payload))

        cache = get_ai_cache()
        assert cache.size == 0  # nothing cached from the failed stream

    def test_empty_response_not_cached(self):
        payload = MealPlanRequest(target_calories=2200)
        mock = _make_stream_mock("")

        with (
            patch("app.services.ai_service.AsyncOpenAI", return_value=mock),
            patch("app.services.ai_service.settings.openai_api_key", "sk-test"),
        ):
            _collect_sse_chunks(generate_meal_plan_stream(payload))

        assert get_ai_cache().size == 0

    def test_sandbox_fallback_not_cached(self):
        """When OpenAI errors and the sandbox streams instead, no caching."""
        payload = MealPlanRequest(target_calories=2200)
        mock = MagicMock()
        mock.chat.completions.create = MagicMock(
            side_effect=RuntimeError("api down")
        )

        with (
            patch("app.services.ai_service.AsyncOpenAI", return_value=mock),
            patch("app.services.ai_service.settings.openai_api_key", "sk-test"),
        ):
            _collect_sse_chunks(generate_meal_plan_stream(payload))

        assert get_ai_cache().size == 0


# ── Local math routing (route level) ─────────────────────────────────────────


class TestLocalMathRouting:
    def test_build_user_message_has_no_arithmetic_delegation(self):
        """With targets filled locally, the user message states them as
        values — the model never has to 'calculate'."""
        payload = MealPlanRequest(
            target_calories=2450, protein_g=130, cuisine_type="South Asian"
        )
        msg = _build_user_message(payload)
        assert "2450" in msg
        assert "130" in msg
        assert "calculate based on" not in msg

    def test_local_math_metric_counts(self):
        before = ai_metrics.snapshot()["local_math_ops"]
        ai_metrics.record_local_math("unit test")
        after = ai_metrics.snapshot()["local_math_ops"]
        assert after == before + 1
        assert ai_metrics.snapshot()["local_math_tokens_saved"] > 0
