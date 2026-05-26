"""initial empty migration

Revision ID: 202605260001
Revises:
Create Date: 2026-05-26
"""

from collections.abc import Sequence

revision: str = "202605260001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
