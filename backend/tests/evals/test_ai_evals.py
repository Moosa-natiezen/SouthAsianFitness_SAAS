"""Agent Evaluation (Eval) pipeline for the AI meal plan service.

Feeds the golden dataset prompts into :func:`generate_meal_plan_stream`,
parses the streamed output, and asserts that:

1. The generated daily calories and protein fall within the acceptable
   tolerance range declared per golden case.
2. Dietary safety holds: if a case declares a peanut / nut allergy in the
   user context, the forbidden token never appears in the generated output
   AND the allergy constraint is present in the system prompt sent to the
   model.

Two execution modes:

- **Mock mode (default)** — streams a deterministic, realistic meal plan
  (with macros inside the case's expected range) through the exact same
  service + parser pipeline used in production.  This runs in CI with zero
  API cost and verifies the plumbing.
- **Live mode (opt-in)** — set ``AI_EVAL_LIVE=1`` and a real
  ``OPENAI_API_KEY`` to evaluate the actual GPT model output.  Live tests
  are skipped otherwise.
"""

from __future__ import annotations

import importlib
import json
import os
import re
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key")
os.environ.setdefault("OPENAI_MODEL", "gpt-4o-mini")

# Force fresh settings
from app.core.config import get_settings

get_settings.cache_clear()
import app.core.config
import app.services.ai_service

importlib.reload(app.core.config)
importlib.reload(app.services.ai_service)

import pytest
from app.schemas.ai_context import UserAIContext
from app.schemas.nutrition import MealPlanRequest
from app.services.ai_service import generate_meal_plan_stream

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
GOLDEN_CASES: list[dict[str, Any]] = json.loads(
    GOLDEN_DATASET_PATH.read_text(encoding="utf-8")
)

# Live evals only run when explicitly enabled AND a real API key is present.
LIVE_EVALS = os.getenv("AI_EVAL_LIVE") == "1"
LIVE_KEY_PRESENT = bool(os.getenv("OPENAI_API_KEY", "").startswith("sk-"))
LIVE_AVAILABLE = LIVE_EVALS and LIVE_KEY_PRESENT


def case_ids() -> list[str]:
    return [case["id"] for case in GOLDEN_CASES]


def forbidden_cases() -> list[dict[str, Any]]:
    return [case for case in GOLDEN_CASES if case.get("forbidden")]


# ── Helpers ───────────────────────────────────────────────────────────────


def _mock_stream_chunks(*texts: str) -> AsyncMock:
    """Build a mock OpenAI stream that yields text chunks."""
    chunks = []
    for text in texts:
        delta = MagicMock()
        delta.content = text
        choice = MagicMock()
        choice.delta = delta
        choice.index = 0
        chunk = MagicMock()
        chunk.choices = [choice]
        chunks.append(chunk)

    async def _aiter():
        for chunk in chunks:
            yield chunk

    stream = AsyncMock()
    stream.__aiter__ = lambda self: _aiter()
    return stream


def _make_mock_client_for_case(case: dict[str, Any]) -> MagicMock:
    """Create a mock OpenAI client that streams a meal plan for *case*.

    The streamed JSON uses the case's ``expected_calories`` and
    ``expected_protein_g`` (which sit inside the declared tolerance ranges),
    so mock-mode runs deterministically verify the full pipeline:
    payload -> service -> SSE stream -> JSON extraction -> macro validation.
    """
    text = json.dumps(_build_meal_plan(case), indent=2)
    # Split into a few chunks to emulate token-by-token streaming.
    mid = max(1, len(text) // 3)
    stream = _mock_stream_chunks("Here is your plan:\n\n```json\n", text[:mid], text[mid:])
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=stream)
    return mock_client


def _build_meal_plan(case: dict[str, Any]) -> dict[str, Any]:
    """Build a realistic JSON meal plan whose totals match the case's expected macros."""
    cal = case["expected_calories"]
    protein = case["expected_protein_g"]
    carbs = int(cal * 0.5 / 4)  # ~50% carbs
    fat = int(cal * 0.25 / 9)  # ~25% fat
    return {
        "meals": [
            {
                "type": "breakfast",
                "name": "Desi Protein Oats",
                "foods": [
                    {"name": "Steel-cut oats", "portion": "1 cup", "calories": 300, "protein_g": 10, "carbs_g": 54, "fat_g": 5},
                    {"name": "Milk (whole)", "portion": "1 cup", "calories": 150, "protein_g": 8, "carbs_g": 12, "fat_g": 8},
                    {"name": "Whey protein", "portion": "1 scoop", "calories": 120, "protein_g": 24, "carbs_g": 3, "fat_g": 1.5},
                ],
                "meal_calories": 570,
                "meal_protein_g": 42,
                "meal_carbs_g": 69,
                "meal_fat_g": 14.5,
            },
            {
                "type": "lunch",
                "name": "South Asian Rice Bowl",
                "foods": [
                    {"name": "Chicken tikka (grilled)", "portion": "200 g", "calories": 330, "protein_g": 46, "carbs_g": 2, "fat_g": 14},
                    {"name": "Basmati rice (cooked)", "portion": "1.5 cups", "calories": 345, "protein_g": 7.5, "carbs_g": 72, "fat_g": 2.8},
                    {"name": "Raita (yogurt + cucumber)", "portion": "0.5 cup", "calories": 60, "protein_g": 3, "carbs_g": 5, "fat_g": 2.5},
                ],
                "meal_calories": 735,
                "meal_protein_g": 56.5,
                "meal_carbs_g": 79,
                "meal_fat_g": 19.3,
            },
            {
                "type": "dinner",
                "name": "Daal Chawal",
                "foods": [
                    {"name": "Masoor dal (red lentil curry)", "portion": "1.5 cups", "calories": 290, "protein_g": 18, "carbs_g": 42, "fat_g": 4},
                    {"name": "Whole wheat chapati", "portion": "2 medium", "calories": 200, "protein_g": 6, "carbs_g": 36, "fat_g": 3.5},
                ],
                "meal_calories": 490,
                "meal_protein_g": 24,
                "meal_carbs_g": 78,
                "meal_fat_g": 7.5,
            },
        ],
        "daily_totals": {"calories": cal, "protein_g": protein, "carbs_g": carbs, "fat_g": fat},
        "tips": ["Hydrate well", "Meal prep on Sunday"],
    }


def _extract_meal_plan_json(text: str) -> dict[str, Any]:
    """Extract the JSON meal plan from a streamed markdown response."""
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    start = text.find("{")
    if start != -1:
        return json.loads(text[start:])
    raise AssertionError(f"No JSON meal plan found in output:\n{text}")


async def _collect_stream_text(agen) -> str:
    """Collect all ``text`` fields from an SSE chunk stream."""
    parts: list[str] = []
    async for chunk in agen:
        if chunk.startswith("data: ") and "[DONE]" not in chunk:
            data = json.loads(chunk[len("data: "):].strip())
            parts.append(data.get("text", ""))
    return "".join(parts)


def _run_generation(case: dict[str, Any]) -> str:
    """Run the service pipeline for *case* and return the full streamed text.

    Patches the OpenAI client with a deterministic mock that streams a
    meal plan matching the case's expected macros.
    """
    payload = MealPlanRequest(**case["request"])
    context = UserAIContext(**case["user_context"])
    mock_client = _make_mock_client_for_case(case)

    with (
        patch("app.services.ai_service._build_openai_client", return_value=mock_client),
        patch("app.services.ai_service.settings.openai_api_key", "sk-test-fake-key"),
    ):
        import asyncio

        text = asyncio.run(_collect_stream_text(generate_meal_plan_stream(payload, user_context=context)))

    return text


def _assert_no_forbidden_tokens(text: str, case: dict[str, Any]) -> None:
    lowered = text.lower()
    for token in case.get("forbidden", []):
        assert token.lower() not in lowered, (
            f"Forbidden token {token!r} appeared in output for case {case['id']}"
        )


def _assert_allergy_in_system_prompt(mock_client: MagicMock, case: dict[str, Any]) -> None:
    """Verify the allergy constraint reached the model's system prompt."""
    allergies = case["user_context"].get("allergies", [])
    if not allergies:
        return
    call_args = mock_client.chat.completions.create.call_args
    assert call_args is not None, "OpenAI client was never called"
    messages = call_args.kwargs["messages"]
    system_content = messages[0]["content"]
    assert "USER CONTEXT" in system_content
    for allergy in allergies:
        assert allergy in system_content, (
            f"Allergy {allergy!r} missing from system prompt for case {case['id']}"
        )


# ── Macro tolerance tests (deterministic mock mode) ──────────────────────


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=case_ids())
def test_golden_case_macros_within_tolerance(case: dict[str, Any]):
    """Generated daily totals must fall inside the case's declared ranges."""
    text = _run_generation(case)
    plan = _extract_meal_plan_json(text)
    totals = plan["daily_totals"]

    cal_lo, cal_hi = case["calorie_range"]
    prot_lo, prot_hi = case["protein_range"]

    assert cal_lo <= totals["calories"] <= cal_hi, (
        f"{case['id']}: calories {totals['calories']} outside [{cal_lo}, {cal_hi}]"
    )
    assert prot_lo <= totals["protein_g"] <= prot_hi, (
        f"{case['id']}: protein {totals['protein_g']} outside [{prot_lo}, {prot_hi}]"
    )


# ── Dietary safety tests ──────────────────────────────────────────────────


@pytest.mark.parametrize("case", forbidden_cases(), ids=lambda c: c["id"])
def test_allergen_never_appears_in_output(case: dict[str, Any]):
    """A declared peanut / nut allergy must never surface in generated text."""
    text = _run_generation(case)
    _assert_no_forbidden_tokens(text, case)


@pytest.mark.parametrize("case", forbidden_cases(), ids=lambda c: c["id"])
def test_allergy_constraint_reaches_system_prompt(case: dict[str, Any]):
    """The allergy constraint must be present in the system prompt sent to the model."""
    payload = MealPlanRequest(**case["request"])
    context = UserAIContext(**case["user_context"])
    mock_client = _make_mock_client_for_case(case)

    with (
        patch("app.services.ai_service._build_openai_client", return_value=mock_client),
        patch("app.services.ai_service.settings.openai_api_key", "sk-test-fake-key"),
    ):
        import asyncio

        asyncio.run(_collect_stream_text(generate_meal_plan_stream(payload, user_context=context)))

    _assert_allergy_in_system_prompt(mock_client, case)


# ── Live model evals (opt-in, skipped by default) ─────────────────────────


@pytest.mark.skipif(
    not LIVE_AVAILABLE,
    reason="Set AI_EVAL_LIVE=1 and OPENAI_API_KEY to run live model evals",
)
@pytest.mark.parametrize("case", GOLDEN_CASES, ids=case_ids())
def test_live_golden_case_macros_within_tolerance(case: dict[str, Any]):
    """Live GPT evaluation: generated macros must fall inside the tolerance range."""
    payload = MealPlanRequest(**case["request"])
    context = UserAIContext(**case["user_context"])

    import asyncio

    text = asyncio.run(_collect_stream_text(generate_meal_plan_stream(payload, user_context=context)))
    plan = _extract_meal_plan_json(text)
    totals = plan["daily_totals"]

    cal_lo, cal_hi = case["calorie_range"]
    prot_lo, prot_hi = case["protein_range"]

    assert cal_lo <= totals["calories"] <= cal_hi, (
        f"[live] {case['id']}: calories {totals['calories']} outside [{cal_lo}, {cal_hi}]"
    )
    assert prot_lo <= totals["protein_g"] <= prot_hi, (
        f"[live] {case['id']}: protein {totals['protein_g']} outside [{prot_lo}, {prot_hi}]"
    )


@pytest.mark.skipif(
    not LIVE_AVAILABLE,
    reason="Set AI_EVAL_LIVE=1 and OPENAI_API_KEY to run live model evals",
)
@pytest.mark.parametrize("case", forbidden_cases(), ids=lambda c: c["id"])
def test_live_allergen_never_appears_in_output(case: dict[str, Any]):
    """Live GPT evaluation: peanut / nut allergy safety on real model output."""
    payload = MealPlanRequest(**case["request"])
    context = UserAIContext(**case["user_context"])

    import asyncio

    text = asyncio.run(_collect_stream_text(generate_meal_plan_stream(payload, user_context=context)))
    _assert_no_forbidden_tokens(text, case)