"""add_goal_reference_identifier_columns

Revision ID: 8af4876fdea2
Revises: d6dbb227ff64
Create Date: 2026-11-01 13:42:47.426739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8af4876fdea2'
down_revision: Union[str, None] = 'd6dbb227ff64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Reference identifier columns helper definition
_IDENTIFIER_COLS = [
    ("identifier_use", sa.Enum("usual", "official", "temp", "secondary", "old", name="identifier_use", create_type=False)),
    ("identifier_type_system", sa.String()),
    ("identifier_type_version", sa.String()),
    ("identifier_type_code", sa.String()),
    ("identifier_type_display", sa.String()),
    ("identifier_type_text", sa.String()),
    ("identifier_type_user_selected", sa.Boolean()),
    ("identifier_system", sa.String()),
    ("identifier_value", sa.String()),
    ("identifier_period_start", sa.DateTime(timezone=True)),
    ("identifier_period_end", sa.DateTime(timezone=True)),
]


def upgrade() -> None:
    op.alter_column("goal", "subject_reference", existing_type=sa.String(), nullable=True)
    op.alter_column(
        "goal",
        "subject_type",
        existing_type=sa.Enum("Patient", "Group", "Organization", name="goal_subject_reference_type"),
        nullable=True,
    )

    # 1. Main goal table: subject, expressed_by
    for prefix in ("subject", "expressed_by"):
        for suffix, col_type in _IDENTIFIER_COLS:
            op.add_column("goal", sa.Column(f"{prefix}_{suffix}", col_type, nullable=True))

    # 2. Reference list tables: addresses, outcome_reference
    for table in ("goal_addresses", "goal_outcome_reference"):
        for suffix, col_type in _IDENTIFIER_COLS:
            op.add_column(table, sa.Column(f"reference_{suffix}", col_type, nullable=True))

    # 3. Note table: author
    for suffix, col_type in _IDENTIFIER_COLS:
        op.add_column("goal_note", sa.Column(f"author_{suffix}", col_type, nullable=True))


def downgrade() -> None:
    for suffix, _ in reversed(_IDENTIFIER_COLS):
        op.drop_column("goal_note", f"author_{suffix}")

    for table in ("goal_outcome_reference", "goal_addresses"):
        for suffix, _ in reversed(_IDENTIFIER_COLS):
            op.drop_column(table, f"reference_{suffix}")

    for prefix in ("expressed_by", "subject"):
        for suffix, _ in reversed(_IDENTIFIER_COLS):
            op.drop_column("goal", f"{prefix}_{suffix}")
