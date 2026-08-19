"""add resume id to requirement matches

Revision ID: 20260818_0002
Revises: 20260818_0001
Create Date: 2026-08-18 00:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_0002"
down_revision: str | None = "20260818_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("requirement_matches", sa.Column("resume_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_requirement_matches_resume_id_resumes",
        "requirement_matches",
        "resumes",
        ["resume_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_requirement_matches_resume_id_resumes",
        "requirement_matches",
        type_="foreignkey",
    )
    op.drop_column("requirement_matches", "resume_id")
