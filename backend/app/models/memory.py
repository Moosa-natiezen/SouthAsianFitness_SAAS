"""User semantic memory model.

Stores long-term memories with vector embeddings for semantic search.
Uses pgvector for efficient cosine similarity retrieval.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class UserMemory(UUIDPrimaryKeyMixin, Base):
    """A long-term memory for a user with vector embedding for semantic search.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the users table.
        content: The memory content (e.g., "User has lower back pain during deadlifts").
        embedding: Vector embedding (1536 dimensions for text-embedding-3-small).
        created_at: Timestamp when the memory was created.
    """

    __tablename__ = "user_memories"

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship to User
    user = relationship("User", back_populates="memories")
