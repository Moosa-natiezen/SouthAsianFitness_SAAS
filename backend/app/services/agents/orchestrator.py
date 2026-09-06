"""Orchestrator Agent.

Central routing agent that analyzes user intent, dispatches to specialized
workers (NutritionWorker, WorkoutWorker), and synthesizes results for
multi-domain queries.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator

from langfuse import observe, propagate_attributes
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.schemas.ai_context import UserAIContext
from app.services.agents.base import BaseWorker, WorkerDomain
from app.services.agents.nutrition_worker import NutritionWorker
from app.services.agents.workout_worker import WorkoutWorker
from app.services.memory_service import retrieve_relevant_memories

logger = get_logger(__name__)


# ── Routing Decision ───────────────────────────────────────────────────────


class RoutingDecision:
    """Encapsulates the Orchestrator's routing analysis."""

    __slots__ = ("confidence", "domains", "reasoning")

    def __init__(
        self,
        domains: list[WorkerDomain],
        confidence: float,
        reasoning: str,
    ) -> None:
        self.domains = domains
        self.confidence = confidence
        self.reasoning = reasoning

    def __repr__(self) -> str:
        return (
            f"RoutingDecision(domains={[d.value for d in self.domains]}, "
            f"confidence={self.confidence:.2f}, reasoning={self.reasoning!r})"
        )


# ── Orchestrator ───────────────────────────────────────────────────────────


class OrchestratorAgent:
    """Main entry point for user AI requests.

    Analyzes user input, determines which domain(s) to route to, and
    dispatches subtasks to specialized workers. For multi-domain queries
    (e.g., "give me a meal plan and a workout"), it runs workers in parallel
    and synthesizes the results.

    Architecture::

        User Request
              │
              ▼
        ┌─────────────┐
        │ Orchestrator │ ◄── Intent Classification
        └──────┬──────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
    ┌────────┐   ┌────────┐
    │Nutri-  │   │Workout │
    │tion    │   │Worker  │
    │Worker  │   │        │
    └────────┘   └────────┘
    """

    def __init__(self) -> None:
        self._workers: dict[WorkerDomain, BaseWorker] = {
            WorkerDomain.NUTRITION: NutritionWorker(),
            WorkerDomain.WORKOUT: WorkoutWorker(),
        }

    @property
    def workers(self) -> list[BaseWorker]:
        """Return all registered workers."""
        return list(self._workers.values())

    @observe()
    def classify_intent(self, user_message: str) -> RoutingDecision:
        """Analyze user message and determine which workers to dispatch to.

        Uses keyword-based scoring with a confidence threshold. If multiple
        domains score above the threshold, the query is treated as multi-domain.

        Args:
            user_message: The user's natural language request.

        Returns:
            A RoutingDecision with the target domains and confidence score.
        """
        scores: dict[WorkerDomain, float] = {}
        for worker in self._workers.values():
            score = worker.matches_intent(user_message)
            scores[worker.domain] = score

        # Threshold: a domain must score >= 0.2 to be considered
        THRESHOLD = 0.2
        selected = [
            domain for domain, score in scores.items()
            if score >= THRESHOLD
        ]

        # If no domain matches, fall back to highest-scoring domain
        if not selected:
            best_domain = max(scores, key=scores.get)  # type: ignore[arg-type]
            selected = [best_domain]
            confidence = scores[best_domain]
            reasoning = f"No strong match; fallback to {best_domain.value} (score={confidence:.2f})"
        elif len(selected) == 1:
            confidence = scores[selected[0]]
            reasoning = f"Single domain match: {selected[0].value} (score={confidence:.2f})"
        else:
            # Multi-domain: pick the two highest
            selected = sorted(selected, key=lambda d: scores[d], reverse=True)[:2]
            confidence = max(scores[d] for d in selected)
            reasoning = (
                f"Multi-domain query: {[d.value for d in selected]} "
                f"(scores={', '.join(f'{d.value}={scores[d]:.2f}' for d in selected)})"
            )

        return RoutingDecision(
            domains=selected,
            confidence=confidence,
            reasoning=reasoning,
        )

    @observe()
    async def dispatch(
        self,
        user_message: str,
        user_context: UserAIContext | None = None,
        user_id: str | None = None,
        db: Session | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Route and dispatch user request to appropriate worker(s).

        For single-domain queries, delegates to the matching worker.
        For multi-domain queries, runs workers in parallel and streams
        results with domain separators.

        Args:
            user_message: The user's natural language request.
            user_context: Persistent user context for personalization.
            user_id: Optional user ID for Langfuse trace attribution.
            db: Optional database session for memory retrieval.
            **kwargs: Additional parameters forwarded to workers.

        Yields:
            SSE-formatted strings from the dispatched worker(s).
        """
        # Retrieve relevant memories if user_id and db are provided
        enriched_context = user_context
        if user_id and db and user_context:
            try:
                from uuid import UUID as _UUID

                memories = await retrieve_relevant_memories(
                    user_id=_UUID(user_id) if isinstance(user_id, str) else user_id,
                    query=user_message,
                    db=db,
                    limit=3,
                )
                if memories:
                    # Add memories to the user context for prompt injection
                    enriched_context = user_context.model_copy(
                        update={"memories": memories}
                    )
            except (ValueError, RuntimeError) as exc:
                logger.warning("Failed to retrieve memories: %s", exc)

        # Use propagate_attributes to set user_id for all nested observations
        # This ensures all child spans (workers, LLM calls) inherit the user_id
        with propagate_attributes(user_id=user_id) if user_id else _no_op_context():
            decision = self.classify_intent(user_message)

            logger.info(
                "[Orchestrator] Routing: %s (confidence=%.2f)",
                decision.reasoning, decision.confidence,
            )

            if len(decision.domains) == 1:
                # Single domain — direct delegation
                worker = self._workers[decision.domains[0]]
                async for chunk in worker.generate_stream(
                    user_message, user_context=enriched_context, **kwargs,
                ):
                    yield chunk
            else:
                # Multi-domain — parallel dispatch with synthesis header
                yield self._sse({
                    "text": (
                        f"## 🔄 Generating {len(decision.domains)} plans for you...\n\n"
                        f"*Routing to: {', '.join(d.value for d in decision.domains)}*\n\n"
                        "---\n\n"
                    ),
                })

                # Run workers in parallel
                tasks = []
                for domain in decision.domains:
                    worker = self._workers[domain]
                    tasks.append(
                        self._collect_worker_output(
                            worker, user_message, enriched_context, **kwargs,
                        )
                    )

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Stream results sequentially with section separators
                for i, (domain, result) in enumerate(zip(decision.domains, results)):
                    worker_name = domain.value.replace("_", " ").title()

                    if isinstance(result, Exception):
                        logger.error(
                            "[Orchestrator] Worker %s failed: %s",
                            domain.value, result,
                        )
                        yield self._sse({
                            "text": f"\n\n## ❌ {worker_name} Generation Failed\n\n*{result!s}*\n\n---\n\n",
                        })
                        continue

                    # Section header
                    if i > 0:
                        yield self._sse({"text": "\n\n---\n\n"})

                    yield self._sse({
                        "text": f"## 📋 {worker_name} Plan\n\n",
                    })

                    # Stream the worker's output
                    for chunk in result:
                        yield chunk

                yield "data: [DONE]\n\n"

    async def _collect_worker_output(
        self,
        worker: BaseWorker,
        user_message: str,
        user_context: UserAIContext | None = None,
        **kwargs,
    ) -> list[str]:
        """Collect all SSE chunks from a worker into a list.

        Used for parallel execution — we buffer the output so we can
        stream it sequentially with proper section headers.
        """
        chunks: list[str] = []
        try:
            async for chunk in worker.generate_stream(
                user_message, user_context=user_context, **kwargs,
            ):
                chunks.append(chunk)
        except Exception as exc:
            logger.error("[Orchestrator] Worker %s error: %s", worker.domain.value, exc)
            raise
        return chunks

    @staticmethod
    def _sse(data: dict) -> str:
        """Format data as an SSE line."""
        return f"data: {json.dumps(data)}\n\n"


# ── Helpers ────────────────────────────────────────────────────────────────


class _NoOpContext:
    """No-op context manager for when user_id is not provided."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _no_op_context() -> _NoOpContext:
    """Return a no-op context manager."""
    return _NoOpContext()
