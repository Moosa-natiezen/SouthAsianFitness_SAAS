"""Orchestrator-Worker multi-agent system for AI generation.

Provides specialized worker agents (NutritionWorker, WorkoutWorker) and
an OrchestratorAgent that routes user requests to the correct domain agents.
"""

from __future__ import annotations

from app.services.agents.base import BaseWorker
from app.services.agents.nutrition_worker import NutritionWorker
from app.services.agents.orchestrator import OrchestratorAgent
from app.services.agents.workout_worker import WorkoutWorker

__all__ = [
    "BaseWorker",
    "NutritionWorker",
    "OrchestratorAgent",
    "WorkoutWorker",
]
