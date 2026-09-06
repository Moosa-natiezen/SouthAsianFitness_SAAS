"""Semantic memory service for long-term user memory.

Provides functions to save and retrieve user memories using vector embeddings
for semantic search. Uses OpenAI's text-embedding-3-small model for embeddings
and pgvector for efficient cosine similarity search.
"""

from __future__ import annotations

from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.memory import UserMemory

logger = get_logger(__name__)

# Embedding model configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def _get_openai_client() -> AsyncOpenAI:
    """Create an OpenAI client for embedding generation."""
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def _generate_embedding(text: str) -> list[float]:
    """Generate an embedding vector for the given text.

    Args:
        text: The text to embed.

    Returns:
        A list of floats representing the embedding vector.
    """
    client = _get_openai_client()
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        dimensions=EMBEDDING_DIMENSIONS,
    )
    return response.data[0].embedding


async def save_user_memory(
    user_id: UUID,
    text: str,
    db: Session,
) -> UserMemory:
    """Save a new memory for a user with its vector embedding.

    Args:
        user_id: The UUID of the user.
        text: The memory content to store.
        db: Active SQLAlchemy session.

    Returns:
        The created UserMemory record.
    """
    # Generate embedding for the memory text
    embedding = await _generate_embedding(text)

    # Create and save the memory record
    memory = UserMemory(
        user_id=user_id,
        content=text,
        embedding=embedding,
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)

    logger.info(
        "Saved memory for user %s: '%s' (embedding dimensions=%d)",
        user_id,
        text[:50] + "..." if len(text) > 50 else text,
        len(embedding),
    )

    return memory


async def retrieve_relevant_memories(
    user_id: UUID,
    query: str,
    db: Session,
    limit: int = 3,
) -> list[str]:
    """Retrieve the most relevant memories for a query using cosine similarity.

    Performs a vector similarity search filtered by user_id to ensure
    users can only access their own memories.

    Args:
        user_id: The UUID of the user to retrieve memories for.
        query: The query text to find relevant memories for.
        db: Active SQLAlchemy session.
        limit: Maximum number of memories to return (default: 3).

    Returns:
        A list of memory content strings, ordered by relevance.
    """
    # Generate embedding for the query
    query_embedding = await _generate_embedding(query)

    # Perform cosine distance search filtered by user_id
    # pgvector's cosine_distance operator: embedding <=> query_embedding
    # Lower distance = more similar
    stmt = (
        select(UserMemory.content)
        .where(UserMemory.user_id == user_id)
        .order_by(UserMemory.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )

    result = db.execute(stmt)
    memories = [row[0] for row in result.all()]

    logger.debug(
        "Retrieved %d relevant memories for user %s (query: '%s')",
        len(memories),
        user_id,
        query[:30] + "..." if len(query) > 30 else query,
    )

    return memories


def format_memories_for_prompt(memories: list[str]) -> str:
    """Format retrieved memories as a section for the LLM system prompt.

    Args:
        memories: List of memory content strings.

    Returns:
        A formatted string suitable for inclusion in a system prompt,
        or an empty string if no memories are provided.
    """
    if not memories:
        return ""

    lines = ["# RELEVANT PAST MEMORIES", ""]
    for i, memory in enumerate(memories, 1):
        lines.append(f"{i}. {memory}")

    return "\n".join(lines)
