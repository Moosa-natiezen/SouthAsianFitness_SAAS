"""merge migration heads

Revision ID: be7198ae526d
Revises: 20260906_0011, c895ba085173
Create Date: 2026-09-06 16:36:52.247825

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "be7198ae526d"
down_revision: str | Sequence[str] | None = ("20260906_0011", "c895ba085173")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
