"""Tests for the strict South Asian / Desi prompt constraints.

Verifies that the AI meal-plan generator (both the /ai streaming route and
the orchestrator's nutrition worker, which share one prompt) mandates
authentic Desi cuisine and cannot drift to generic Western fitness meals
when the cuisine field is omitted.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

from unittest.mock import patch

from app.schemas.nutrition import MealPlanRequest
from app.services.ai_service import SYSTEM_PROMPT, _build_user_message

# ── System prompt mandate ────────────────────────────────────────────────────


class TestSystemPromptMandate:
    def test_expert_role_is_south_asian_nutritionist(self):
        assert "expert South Asian sports nutritionist" in SYSTEM_PROMPT

    def test_desi_dishes_listed(self):
        """The prompt names traditional dishes the model must use."""
        for dish in [
            "Roti",
            "Paratha",
            "Daal",
            "Paneer",
            "Chana",
            "Karahi",
            "Tikka",
            "Sabzi",
            "Biryani",
            "Pulao",
            "Haleem",
        ]:
            assert dish in SYSTEM_PROMPT, f"missing dish: {dish}"

    def test_western_drift_explicitly_forbidden(self):
        """The classic Western fitness meals are called out as forbidden."""
        assert "plain grilled chicken" in SYSTEM_PROMPT
        assert "broccoli" in SYSTEM_PROMPT
        assert "plain oats" in SYSTEM_PROMPT
        assert "egg-white" in SYSTEM_PROMPT
        # Exception only when the user explicitly asks for that dish
        assert "explicitly requests" in SYSTEM_PROMPT

    def test_no_western_snack_escape_hatch(self):
        """The old 'Greek yogurt / protein shakes' snack line is gone —
        it was the main loophole letting Western snacks in."""
        assert "Greek yogurt" not in SYSTEM_PROMPT
        assert "almonds" not in SYSTEM_PROMPT

    def test_traditional_meal_titles_required(self):
        """Output JSON meal names must be traditional dish titles."""
        assert "traditional dish name" in SYSTEM_PROMPT
        assert "never generic descriptions" in SYSTEM_PROMPT

    def test_output_schema_unchanged(self):
        """The JSON schema contract (meals/foods/daily_totals) is preserved."""
        for key in ['"meals"', '"foods"', '"daily_totals"', '"portion"', '"protein_g"']:
            assert key in SYSTEM_PROMPT, f"missing schema key: {key}"

    def test_regional_cuisines_still_named(self):
        """Regional identity retained (existing tests assert on these)."""
        assert "Pakistani" in SYSTEM_PROMPT
        assert "Indian" in SYSTEM_PROMPT
        assert "Bangladeshi" in SYSTEM_PROMPT


# ── Cuisine default injection ────────────────────────────────────────────────


class TestCuisineDefaultInjection:
    def test_omitted_cuisine_defaults_to_south_asian(self):
        """A request without cuisine_type still pins Desi in the user message."""
        payload = MealPlanRequest(target_calories=2200, cuisine_type=None)
        msg = _build_user_message(payload)
        assert "Preferred cuisine: South Asian (Desi)" in msg

    def test_explicit_cuisine_is_used_verbatim(self):
        payload = MealPlanRequest(target_calories=2200, cuisine_type="Mediterranean")
        msg = _build_user_message(payload)
        assert "Preferred cuisine: Mediterranean" in msg
        assert "South Asian (Desi)" not in msg


# ── Worker shares the same prompt (no drift) ─────────────────────────────────


class TestWorkerPromptDeduplication:
    def test_worker_imports_canonical_prompt(self):
        """The nutrition worker must use ai_service.SYSTEM_PROMPT, not a copy.

        Compared by value, not identity: test_ai_streaming reloads
        app.services.ai_service at import time, which rebinds SYSTEM_PROMPT
        to a new object — a known suite-wide isolation quirk. Value equality
        still proves the worker has no drifted copy.
        """
        from app.services.agents.nutrition_worker import NUTRITION_SYSTEM_PROMPT

        assert NUTRITION_SYSTEM_PROMPT == SYSTEM_PROMPT
        assert "NON-NEGOTIABLE CUISINE MANDATE" in NUTRITION_SYSTEM_PROMPT

    def test_worker_user_content_pins_cuisine_when_omitted(self):
        from app.services.agents.nutrition_worker import NutritionWorker

        worker = NutritionWorker()
        content = worker._build_user_content("make me a plan", {})
        assert "Preferred cuisine: South Asian (Desi)" in content


# ── End-to-end: prompt reaches the model ─────────────────────────────────────


class TestPromptReachesModel:
    def test_system_prompt_contains_mandate_on_route(self):
        """E2E: the strict mandate is in the system message sent to OpenAI."""
        from fastapi.testclient import TestClient
        from tests.test_ai_streaming import (
            _make_openai_stream_response,
            setup_pro_client,
        )

        client: TestClient = setup_pro_client()
        mock_client = _make_openai_stream_response("plan")

        with (
            patch("app.services.ai_service.AsyncOpenAI", return_value=mock_client),
            patch("app.services.ai_service.settings.openai_api_key", "sk-test-fake-key"),
        ):
            resp = client.post("/api/ai/meal-plans/generate", json={})

        assert resp.status_code == 200
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_msg = messages[0]["content"]
        user_msg = messages[1]["content"]

        # Mandate reached the model
        assert "NON-NEGOTIABLE CUISINE MANDATE" in system_msg
        assert "MUST be authentic South Asian / Desi cuisine" in system_msg
        # Cuisine pinned even with an empty body
        assert "Preferred cuisine: South Asian (Desi)" in user_msg
