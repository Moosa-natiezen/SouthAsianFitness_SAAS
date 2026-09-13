"""Lightweight in-memory metrics for the AI generation pipeline.

Tracks the cost-side of AI usage: LLM calls made, cache hits, estimated
tokens saved by serving cached responses, and arithmetic handled locally
by Python instead of the LLM (zero tokens). Counters are process-local —
good enough for cost observability at this scale; export to Prometheus or
Langfuse later if aggregation across workers is needed.

The token-saved estimate uses the industry-standard ~4 characters per
token heuristic (OpenAI docs suggest ~4 chars/token for English prose).
"""

from __future__ import annotations

from threading import Lock

from app.core.logging import get_logger

logger = get_logger(__name__)

# ~4 characters per token is the standard estimation heuristic for English.
_CHARS_PER_TOKEN = 4


class AICostMetrics:
    """Thread-safe, process-local counters for AI cost optimization."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._llm_calls = 0
        self._cache_hits = 0
        self._cache_tokens_saved = 0
        self._local_math_ops = 0
        self._local_math_tokens_saved = 0

    def record_llm_call(self, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        """Record an actual LLM call (tokens billed)."""
        with self._lock:
            self._llm_calls += 1

    def record_cache_hit(self, response_chars: int) -> None:
        """Record serving a response from cache.

        Estimates tokens saved as the full response that did NOT need to be
        generated (the ~100-token prompt is still needed to build the cached
        key, so it is deliberately not counted as saved).
        """
        saved = max(1, response_chars // _CHARS_PER_TOKEN)
        with self._lock:
            self._cache_hits += 1
            self._cache_tokens_saved += saved
        logger.info(
            "AI_CACHE_HIT: served cached meal plan (~%d tokens saved)",
            saved,
        )

    def record_local_math(self, description: str = "") -> None:
        """Record arithmetic performed locally instead of by the LLM.

        Each macro-math block we keep out of the prompt/response saves both
        the tokens to describe the computation and the tokens for the model
        to (unreliably) do it.
        """
        with self._lock:
            self._local_math_ops += 1
            self._local_math_tokens_saved += _LOCAL_MATH_TOKENS_SAVED_PER_OP
        if description:
            logger.info(
                "AI_LOCAL_MATH: %s (~%d tokens saved)",
                description,
                _LOCAL_MATH_TOKENS_SAVED_PER_OP,
            )

    @property
    def llm_calls(self) -> int:
        return self._llm_calls

    @property
    def cache_hits(self) -> int:
        return self._cache_hits

    @property
    def cache_tokens_saved(self) -> int:
        return self._cache_tokens_saved

    @property
    def local_math_ops(self) -> int:
        return self._local_math_ops

    @property
    def local_math_tokens_saved(self) -> int:
        return self._local_math_tokens_saved

    @property
    def total_tokens_saved(self) -> int:
        return self._cache_tokens_saved + self._local_math_tokens_saved

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {
                "llm_calls": self._llm_calls,
                "cache_hits": self._cache_hits,
                "cache_hits_tokens_saved": self._cache_tokens_saved,
                "local_math_ops": self._local_math_ops,
                "local_math_tokens_saved": self._local_math_tokens_saved,
                "total_tokens_saved": self.total_tokens_saved,
            }

    def reset(self) -> None:
        """Reset all counters (tests, admin tools)."""
        with self._lock:
            self._llm_calls = 0
            self._cache_hits = 0
            self._cache_tokens_saved = 0
            self._local_math_ops = 0
            self._local_math_tokens_saved = 0


# A macro-math block (targets + per-meal + daily totals) is roughly this
# many tokens if the LLM had to compute and emit it instead of Python.
_LOCAL_MATH_TOKENS_SAVED_PER_OP = 40


# Process-wide singleton.
ai_metrics = AICostMetrics()
