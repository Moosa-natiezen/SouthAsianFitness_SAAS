"""Tests for the OrchestratorAgent multi-agent routing system."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from app.schemas.ai_context import UserAIContext
from app.services.agents.base import WorkerDomain
from app.services.agents.nutrition_worker import NutritionWorker
from app.services.agents.orchestrator import OrchestratorAgent
from app.services.agents.workout_worker import WorkoutWorker

# ── Helpers ────────────────────────────────────────────────────────────────


async def _collect(gen: AsyncGenerator[str, None]) -> list[str]:
    """Collect all items from an async generator."""
    return [item async for item in gen]


def _collect_sync(gen: AsyncGenerator[str, None]) -> list[str]:
    """Synchronous wrapper for async generator collection."""
    return asyncio.run(_collect(gen))


# ── Worker Unit Tests ──────────────────────────────────────────────────────


class TestNutritionWorker:
    """Tests for NutritionWorker domain matching and properties."""

    def test_domain_is_nutrition(self) -> None:
        worker = NutritionWorker()
        assert worker.domain == WorkerDomain.NUTRITION

    def test_keywords_include_core_terms(self) -> None:
        worker = NutritionWorker()
        for kw in ["meal", "food", "diet", "calories", "protein"]:
            assert kw in worker.keywords

    def test_matches_meal_plan_request(self) -> None:
        worker = NutritionWorker()
        score = worker.matches_intent("Create a meal plan for me")
        assert score > 0.5

    def test_matches_food_query(self) -> None:
        worker = NutritionWorker()
        score = worker.matches_intent("What should I eat for breakfast?")
        assert score > 0.3

    def test_low_score_for_workout_query(self) -> None:
        worker = NutritionWorker()
        score = worker.matches_intent("Generate a push pull legs workout")
        assert score < 0.3


class TestWorkoutWorker:
    """Tests for WorkoutWorker domain matching and properties."""

    def test_domain_is_workout(self) -> None:
        worker = WorkoutWorker()
        assert worker.domain == WorkerDomain.WORKOUT

    def test_keywords_include_core_terms(self) -> None:
        worker = WorkoutWorker()
        for kw in ["workout", "exercise", "training", "gym", "strength"]:
            assert kw in worker.keywords

    def test_matches_workout_request(self) -> None:
        worker = WorkoutWorker()
        score = worker.matches_intent("Create a workout plan for hypertrophy")
        assert score > 0.5

    def test_low_score_for_meal_query(self) -> None:
        worker = WorkoutWorker()
        score = worker.matches_intent("What should I eat for lunch?")
        assert score < 0.3


# ── Orchestrator Routing Tests ─────────────────────────────────────────────


class TestOrchestratorClassification:
    """Tests for OrchestratorAgent intent classification."""

    def setup_method(self) -> None:
        self.orchestrator = OrchestratorAgent()

    def test_nutrition_only_query(self) -> None:
        decision = self.orchestrator.classify_intent("Create a meal plan for weight loss")
        assert WorkerDomain.NUTRITION in decision.domains
        assert decision.confidence > 0.3

    def test_workout_only_query(self) -> None:
        decision = self.orchestrator.classify_intent("Generate a hypertrophy workout routine")
        assert WorkerDomain.WORKOUT in decision.domains
        assert decision.confidence > 0.3

    def test_multi_domain_query(self) -> None:
        decision = self.orchestrator.classify_intent(
            "I need a meal plan and a workout program"
        )
        # Both domains should be selected
        assert len(decision.domains) >= 2
        assert WorkerDomain.NUTRITION in decision.domains
        assert WorkerDomain.WORKOUT in decision.domains

    def test_fallback_for_ambiguous_query(self) -> None:
        # Very ambiguous query — should still route somewhere
        decision = self.orchestrator.classify_intent("Help me get fit")
        assert len(decision.domains) >= 1
        assert decision.confidence >= 0.0

    def test_routing_decision_repr(self) -> None:
        decision = self.orchestrator.classify_intent("meal plan")
        repr_str = repr(decision)
        assert "RoutingDecision" in repr_str
        assert "domains" in repr_str

    def test_explicit_meal_plan_boost(self) -> None:
        decision = self.orchestrator.classify_intent("Create a meal plan for me")
        assert WorkerDomain.NUTRITION in decision.domains

    def test_explicit_workout_boost(self) -> None:
        decision = self.orchestrator.classify_intent("Generate a workout plan")
        assert WorkerDomain.WORKOUT in decision.domains


class TestOrchestratorDispatch:
    """Tests for OrchestratorAgent dispatch behavior."""

    def setup_method(self) -> None:
        self.orchestrator = OrchestratorAgent()

    def test_dispatch_single_domain(self) -> None:
        """Single-domain queries should stream from one worker."""
        chunks = _collect_sync(
            self.orchestrator.dispatch("Create a meal plan for me")
        )
        # Should have at least the sandbox flag and some content
        assert len(chunks) > 0
        # First chunk should be sandbox flag
        import json
        first_data = json.loads(chunks[0].removeprefix("data: ").strip())
        assert first_data.get("sandbox") is True

    def test_dispatch_multi_domain_sequential(self) -> None:
        """Multi-domain queries should produce output from both workers."""
        chunks = _collect_sync(
            self.orchestrator.dispatch(
                "Give me a meal plan and a workout program"
            )
        )
        # Should have routing header + output from both workers + [DONE]
        assert len(chunks) > 5
        # Should contain the multi-plan routing header
        all_text = "".join(chunks)
        assert "Generating" in all_text or "plans" in all_text

    def test_dispatch_with_context(self) -> None:
        """User context should be passed through to workers."""
        from uuid import uuid4

        context = UserAIContext(
            user_id=uuid4(),
            target_calories=2200,
            target_protein=140,
            current_goal="cutting",
        )
        chunks = _collect_sync(
            self.orchestrator.dispatch(
                "Create a meal plan for me",
                user_context=context,
            )
        )
        assert len(chunks) > 0
