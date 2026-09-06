"""Loop engineering safeguards for AI streaming.

Provides a reusable guard to prevent infinite agentic loops and runaway
token usage in streaming endpoints. The guard tracks iteration steps and
terminates gracefully when a budget is exceeded.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class MaxIterationsExceededError(Exception):
    """Raised when an agent loop exceeds its maximum iteration budget."""


class AgentLoopGuard:
    """A guard that tracks iterations and terminates loops exceeding a budget.

    Usage::

        guard = AgentLoopGuard(max_iterations=5)
        async for chunk in stream:
            guard.tick()
            if guard.exceeded:
                logger.warning("Loop budget exceeded, terminating")
                break
            yield chunk

    Or using the ``limit_reached`` property::

        guard = AgentLoopGuard(max_iterations=6)
        while not guard.limit_reached:
            guard.tick()
            # do work
            yield result
    """

    def __init__(self, max_iterations: int = 5) -> None:
        self.max_iterations = max_iterations
        self._current = 0

    @property
    def current(self) -> int:
        """Current iteration count."""
        return self._current

    @property
    def exceeded(self) -> bool:
        """True if the iteration budget has been exceeded."""
        return self._current >= self.max_iterations

    @property
    def limit_reached(self) -> bool:
        """Alias for ``exceeded`` for while-loop semantics."""
        return self.exceeded

    def tick(self) -> int:
        """Increment the iteration counter and return the new count.

        Raises ``MaxIterationsExceededError`` if the budget is exceeded after
        the increment.
        """
        self._current += 1
        if self.exceeded:
            raise MaxIterationsExceededError(
                f"Loop exceeded maximum of {self.max_iterations} iterations"
            )
        return self._current

    def reset(self) -> None:
        """Reset the counter to zero (e.g. for reuse across requests)."""
        self._current = 0


async def stream_with_loop_guard(
    stream: AsyncGenerator[Any, None],
    max_iterations: int = 5,
    error_message: str = "Generation terminated: loop budget exceeded",
) -> AsyncGenerator[Any, None]:
    """Wrap an async generator with a loop guard.

    This is a convenience wrapper that yields items from *stream* until the
    loop guard exceeds its budget. When the budget is hit, it logs a warning
    and yields a final error payload instead of raising.

    Args:
        stream: The async generator to wrap.
        max_iterations: Maximum number of chunks/items before termination.
        error_message: Message to include in the final error payload.

    Yields:
        Items from the wrapped stream, or a final error dict if the budget
        is exceeded.
    """
    guard = AgentLoopGuard(max_iterations=max_iterations)
    try:
        async for item in stream:
            yield item
            guard.tick()
    except MaxIterationsExceededError:
        logger.warning(
            "Loop guard terminated stream after %d iterations: %s",
            guard.current,
            error_message,
        )
        # Yield a final error payload so the client knows generation was
        # truncated rather than crashed.
        yield {"error": True, "message": error_message}
