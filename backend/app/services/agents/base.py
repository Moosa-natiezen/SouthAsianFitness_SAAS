"""Base worker agent interface.

All domain-specific workers (Nutrition, Workout) inherit from BaseWorker,
which defines the contract for capability declaration and stream generation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from enum import Enum

from app.core.logging import get_logger
from app.schemas.ai_context import UserAIContext

logger = get_logger(__name__)


class WorkerDomain(str, Enum):
    """Domain identifiers for routing."""

    NUTRITION = "nutrition"
    WORKOUT = "workout"
    GENERAL = "general"


class BaseWorker(ABC):
    """Abstract base class for all domain workers.

    Each worker declares its domain and keywords so the Orchestrator can
    route requests. Workers produce SSE-streamed responses.
    """

    @property
    @abstractmethod
    def domain(self) -> WorkerDomain:
        """Return the worker's domain identifier."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of what this worker handles."""
        ...

    @property
    @abstractmethod
    def keywords(self) -> list[str]:
        """Keywords used for intent classification / routing."""
        ...

    @abstractmethod
    async def generate_stream(
        self,
        user_message: str,
        user_context: UserAIContext | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate an SSE stream for the given user request.

        Args:
            user_message: The user's natural language request.
            user_context: Persistent user context (goals, dietary prefs, etc.).
            **kwargs: Domain-specific parameters (e.g., goal, split, equipment).

        Yields:
            SSE-formatted strings (``data: {...}\\n\\n``).
        """
        ...
        yield  # make this an async generator

    def matches_intent(self, user_message: str) -> float:
        """Return a confidence score (0.0–1.0) that this worker can handle the message.

        Default implementation uses keyword frequency scoring.
        Subclasses can override for more sophisticated routing.
        """
        message_lower = user_message.lower()
        matched = sum(1 for kw in self.keywords if kw in message_lower)
        if not self.keywords:
            return 0.0
        return min(matched / max(len(self.keywords) * 0.3, 1), 1.0)
