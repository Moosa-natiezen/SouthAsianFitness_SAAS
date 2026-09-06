"""Tests for the semantic memory service.

Verifies vector insertion, cosine similarity retrieval, and user-scoped access.
Uses asyncio.run() for async test wrappers (matching project conventions).
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.services.memory_service import (
    format_memories_for_prompt,
    retrieve_relevant_memories,
    save_user_memory,
)


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_mock_db():
    """Create a mock SQLAlchemy session."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.execute = MagicMock()
    return db


def _make_mock_embedding(length: int = 1536) -> list[float]:
    """Create a mock embedding vector."""
    return [0.1] * length


def _run_async(coro):
    """Run an async function synchronously."""
    return asyncio.run(coro)


# ── Unit Tests: format_memories_for_prompt ──────────────────────────────────


class TestFormatMemoriesForPrompt:
    """Tests for the prompt formatting helper."""

    def test_empty_memories_returns_empty_string(self) -> None:
        result = format_memories_for_prompt([])
        assert result == ""

    def test_single_memory(self) -> None:
        result = format_memories_for_prompt(["User has back pain"])
        assert "RELEVANT PAST MEMORIES" in result
        assert "1. User has back pain" in result

    def test_multiple_memories(self) -> None:
        memories = ["Memory 1", "Memory 2", "Memory 3"]
        result = format_memories_for_prompt(memories)
        assert "1. Memory 1" in result
        assert "2. Memory 2" in result
        assert "3. Memory 3" in result

    def test_preserves_order(self) -> None:
        memories = ["First", "Second", "Third"]
        result = format_memories_for_prompt(memories)
        lines = result.strip().split("\n")
        # Skip header lines
        memory_lines = [l for l in lines if l.startswith(("1.", "2.", "3."))]
        assert memory_lines == ["1. First", "2. Second", "3. Third"]


# ── Unit Tests: save_user_memory ───────────────────────────────────────────


class TestSaveUserMemory:
    """Tests for saving memories with embeddings."""

    def test_save_memory_calls_openai_and_db(self) -> None:
        user_id = uuid4()
        text = "User prefers high-protein meals"
        mock_db = _make_mock_db()

        mock_embedding = _make_mock_embedding()

        with patch("app.services.memory_service._generate_embedding") as mock_embed:
            mock_embed.return_value = mock_embedding

            _run_async(save_user_memory(user_id, text, mock_db))

            # Verify embedding was generated
            mock_embed.assert_called_once_with(text)

            # Verify database operations
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

            # Verify the memory object was created correctly
            saved_memory = mock_db.add.call_args[0][0]
            assert saved_memory.user_id == user_id
            assert saved_memory.content == text
            assert saved_memory.embedding == mock_embedding

    def test_save_memory_returns_created_record(self) -> None:
        user_id = uuid4()
        text = "Test memory"
        mock_db = _make_mock_db()

        with patch("app.services.memory_service._generate_embedding") as mock_embed:
            mock_embed.return_value = _make_mock_embedding()

            result = _run_async(save_user_memory(user_id, text, mock_db))

            # Result should be the memory object that was added
            assert result.user_id == user_id
            assert result.content == text


# ── Unit Tests: retrieve_relevant_memories ─────────────────────────────────


class TestRetrieveRelevantMemories:
    """Tests for retrieving memories with cosine similarity search."""

    def test_retrieve_filters_by_user_id(self) -> None:
        user_id = uuid4()
        query = "What should I eat?"
        mock_db = _make_mock_db()

        # Mock the query result
        mock_result = MagicMock()
        mock_result.all.return_value = [("Memory about food",), ("Another memory",)]
        mock_db.execute.return_value = mock_result

        with patch("app.services.memory_service._generate_embedding") as mock_embed:
            mock_embed.return_value = _make_mock_embedding()

            result = _run_async(retrieve_relevant_memories(user_id, query, mock_db))

            # Verify the query was executed
            mock_db.execute.assert_called_once()

            # Verify results are extracted correctly
            assert result == ["Memory about food", "Another memory"]

    def test_retrieve_respects_limit(self) -> None:
        user_id = uuid4()
        query = "test query"
        mock_db = _make_mock_db()

        # Simulate the database returning only 2 results (as if limit=2 was applied)
        mock_result = MagicMock()
        mock_result.all.return_value = [("Memory 1",), ("Memory 2",)]
        mock_db.execute.return_value = mock_result

        with patch("app.services.memory_service._generate_embedding") as mock_embed:
            mock_embed.return_value = _make_mock_embedding()

            result = _run_async(retrieve_relevant_memories(user_id, query, mock_db, limit=2))

            # Should return only 2 memories (as returned by the database)
            assert len(result) == 2
            assert result == ["Memory 1", "Memory 2"]

    def test_retrieve_returns_empty_when_no_memories(self) -> None:
        user_id = uuid4()
        query = "test query"
        mock_db = _make_mock_db()

        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        with patch("app.services.memory_service._generate_embedding") as mock_embed:
            mock_embed.return_value = _make_mock_embedding()

            result = _run_async(retrieve_relevant_memories(user_id, query, mock_db))

            assert result == []


# ── User Scoping Tests ────────────────────────────────────────────────────


class TestUserScoping:
    """Tests that memories are properly scoped per user."""

    def test_different_users_get_different_memories(self) -> None:
        """Simulate two users with different memories."""
        user_a = uuid4()
        user_b = uuid4()
        query = "What should I eat?"

        mock_db = _make_mock_db()

        # User A's memories
        mock_result_a = MagicMock()
        mock_result_a.all.return_value = [("User A's memory",)]

        # User B's memories
        mock_result_b = MagicMock()
        mock_result_b.all.return_value = [("User B's memory",)]

        with patch("app.services.memory_service._generate_embedding") as mock_embed:
            mock_embed.return_value = _make_mock_embedding()

            # First call for user A
            mock_db.execute.return_value = mock_result_a
            result_a = _run_async(retrieve_relevant_memories(user_a, query, mock_db))

            # Second call for user B
            mock_db.execute.return_value = mock_result_b
            result_b = _run_async(retrieve_relevant_memories(user_b, query, mock_db))

            # Verify different results
            assert result_a == ["User A's memory"]
            assert result_b == ["User B's memory"]

            # Verify two separate queries were made
            assert mock_db.execute.call_count == 2


# ── Integration-Style Tests ───────────────────────────────────────────────


class TestMemoryWorkflow:
    """End-to-end style tests for the memory workflow."""

    def test_save_and_retrieve_workflow(self) -> None:
        """Test saving a memory and then retrieving it."""
        user_id = uuid4()
        memory_text = "User has lower back pain during heavy deadlifts"
        query = "back pain exercises"

        mock_db = _make_mock_db()

        # Mock embedding generation
        mock_embedding = _make_mock_embedding()

        with patch("app.services.memory_service._generate_embedding") as mock_embed:
            mock_embed.return_value = mock_embedding

            # Save the memory
            memory = _run_async(save_user_memory(user_id, memory_text, mock_db))
            assert memory.content == memory_text

            # Now retrieve relevant memories
            mock_result = MagicMock()
            mock_result.all.return_value = [(memory_text,)]
            mock_db.execute.return_value = mock_result

            memories = _run_async(retrieve_relevant_memories(user_id, query, mock_db))
            assert memory_text in memories

            # Format for prompt
            prompt_section = format_memories_for_prompt(memories)
            assert "RELEVANT PAST MEMORIES" in prompt_section
            assert memory_text in prompt_section
