"""Tests for loop engineering safeguards (AgentLoopGuard and streaming guards)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from app.services.loop_guard import (
    AgentLoopGuard,
    MaxIterationsExceededError,
    stream_with_loop_guard,
)

# ── AgentLoopGuard unit tests ──────────────────────────────────────────────


class TestAgentLoopGuard:
    """Tests for the AgentLoopGuard class."""

    def test_guard_initializes_with_zero_current(self) -> None:
        guard = AgentLoopGuard(max_iterations=5)
        assert guard.current == 0
        assert guard.max_iterations == 5

    def test_tick_increments_counter(self) -> None:
        guard = AgentLoopGuard(max_iterations=5)
        assert guard.tick() == 1
        assert guard.tick() == 2
        assert guard.current == 2

    def test_exceeded_is_false_under_budget(self) -> None:
        guard = AgentLoopGuard(max_iterations=5)
        guard.tick()
        guard.tick()
        assert guard.exceeded is False
        assert guard.limit_reached is False

    def test_exceeded_is_true_at_budget(self) -> None:
        """After tick() hits max_iterations, exceeded becomes True."""
        guard = AgentLoopGuard(max_iterations=2)
        guard.tick()  # 0 → 1, not exceeded
        with pytest.raises(MaxIterationsExceededError):
            guard.tick()  # 1 → 2, then check: 2 >= 2 → exceeded → raises
        # After the exception, current is still 2 and exceeded is True
        assert guard.current == 2
        assert guard.exceeded is True

    def test_tick_raises_when_limit_reached(self) -> None:
        guard = AgentLoopGuard(max_iterations=2)
        guard.tick()  # 0 → 1
        with pytest.raises(MaxIterationsExceededError):
            guard.tick()  # 1 → 2, raises

    def test_can_tick_max_iterations_minus_one_times(self) -> None:
        """With max_iterations=N, tick() can be called N times (the Nth raises)."""
        guard = AgentLoopGuard(max_iterations=3)
        guard.tick()  # 0 → 1
        guard.tick()  # 1 → 2
        with pytest.raises(MaxIterationsExceededError):
            guard.tick()  # 2 → 3, raises

    def test_reset(self) -> None:
        guard = AgentLoopGuard(max_iterations=3)
        guard.tick()
        guard.tick()
        guard.reset()
        assert guard.current == 0
        assert guard.exceeded is False

    def test_default_max_iterations(self) -> None:
        guard = AgentLoopGuard()
        assert guard.max_iterations == 5

    def test_exception_message(self) -> None:
        guard = AgentLoopGuard(max_iterations=10)
        for _ in range(9):
            guard.tick()  # 0 → 9, not exceeded yet
        with pytest.raises(MaxIterationsExceededError, match="maximum of 10"):
            guard.tick()  # 9 → 10, then 10 >= 10 → exceeded → raises


# ── stream_with_loop_guard tests (sync wrappers using asyncio.run) ─────────


async def _async_collect(gen: AsyncGenerator[Any, None]) -> list[Any]:
    """Collect all items from an async generator into a list."""
    return [item async for item in gen]


def _collect(gen: AsyncGenerator[Any, None]) -> list[Any]:
    """Synchronous wrapper for collecting async generator items."""
    return asyncio.run(_async_collect(gen))


class TestStreamWithLoopGuard:
    """Tests for the stream_with_loop_guard async wrapper."""

    def test_wraps_stream_and_yields_all_items(self) -> None:
        async def fake_stream() -> AsyncGenerator[dict[str, str], None]:
            for i in range(5):
                yield {"text": f"chunk-{i}"}

        results = _collect(stream_with_loop_guard(fake_stream(), max_iterations=10))

        assert len(results) == 5
        assert results[0] == {"text": "chunk-0"}
        assert results[4] == {"text": "chunk-4"}

    def test_terminates_when_budget_exceeded(self) -> None:
        async def infinite_stream() -> AsyncGenerator[dict[str, Any], None]:
            i = 0
            while True:
                yield {"text": f"chunk-{i}"}
                i += 1

        results = _collect(stream_with_loop_guard(infinite_stream(), max_iterations=3))

        # 3 normal chunks + 1 error payload
        assert len(results) == 4
        assert results[0] == {"text": "chunk-0"}
        assert results[2] == {"text": "chunk-2"}
        # The 4th item is the error termination payload
        assert results[3]["error"] is True
        assert "maximum" in results[3]["message"].lower() or "budget" in results[3]["message"].lower()

    def test_empty_stream(self) -> None:
        async def empty_stream() -> AsyncGenerator[dict[str, str], None]:
            return
            yield  # make it an async generator  # type: ignore[misc]

        results = _collect(stream_with_loop_guard(empty_stream(), max_iterations=5))
        assert results == []

    def test_budget_one_yields_one_then_error(self) -> None:
        async def three_items() -> AsyncGenerator[dict[str, str], None]:
            yield {"text": "a"}
            yield {"text": "b"}
            yield {"text": "c"}

        results = _collect(stream_with_loop_guard(three_items(), max_iterations=1))

        assert len(results) == 2  # 1 normal + 1 error
        assert results[0] == {"text": "a"}
        assert results[1]["error"] is True

    def test_high_budget_passes_through(self) -> None:
        """A stream with fewer items than the budget should pass through cleanly."""
        async def short_stream() -> AsyncGenerator[dict[str, str], None]:
            for i in range(3):
                yield {"text": f"item-{i}"}

        results = _collect(stream_with_loop_guard(short_stream(), max_iterations=100))
        assert len(results) == 3
        # No error payload should be present
        assert all("error" not in item for item in results)
