"""add task reference identifier columns

Revision ID: d6dbb227ff64
Revises: 3b7a128e49c1
Create Date: 2026-11-01 13:19:21.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd6dbb227ff64'
down_revision: Union[str, None] = '3b7a128e49c1'
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
    # 1. Main task table: focus, for, encounter, requester, owner, location, reason_reference, group_identifier_assigner
    task_prefixes = (
        "focus",
        "for",
        "encounter",
        "requester",
        "owner",
        "location",
        "reason_reference",
        "group_identifier_assigner",
    )
    for prefix in task_prefixes:
        for suffix, col_type in _IDENTIFIER_COLS:
            op.add_column("task", sa.Column(f"{prefix}_{suffix}", col_type, nullable=True))

    # 2. Reference list tables: based_on, part_of, insurance, relevant_history, restriction_recipient
    ref_tables = [
        "task_based_on",
        "task_part_of",
        "task_insurance",
        "task_relevant_history",
        "task_restriction_recipient",
    ]
    for table in ref_tables:
        for suffix, col_type in _IDENTIFIER_COLS:
            op.add_column(table, sa.Column(f"reference_{suffix}", col_type, nullable=True))

    # 3. Note table: author
    for suffix, col_type in _IDENTIFIER_COLS:
        op.add_column("task_note", sa.Column(f"author_{suffix}", col_type, nullable=True))

    # 4. Input and Output tables: value_reference
    for table in ("task_input", "task_output"):
        for suffix, col_type in _IDENTIFIER_COLS:
            op.add_column(table, sa.Column(f"value_reference_{suffix}", col_type, nullable=True))


def downgrade() -> None:
    task_prefixes = (
        "focus",
        "for",
        "encounter",
        "requester",
        "owner",
        "location",
        "reason_reference",
        "group_identifier_assigner",
    )
    for prefix in reversed(task_prefixes):
        for suffix, _ in reversed(_IDENTIFIER_COLS):
            op.drop_column("task", f"{prefix}_{suffix}")

    ref_tables = [
        "task_based_on",
        "task_part_of",
        "task_insurance",
        "task_relevant_history",
        "task_restriction_recipient",
    ]
    for table in reversed(ref_tables):
        for suffix, _ in reversed(_IDENTIFIER_COLS):
            op.drop_column(table, f"reference_{suffix}")

    for suffix, _ in reversed(_IDENTIFIER_COLS):
        op.drop_column("task_note", f"author_{suffix}")

    for table in ("task_output", "task_input"):
        for suffix, _ in reversed(_IDENTIFIER_COLS):
            op.drop_column(table, f"value_reference_{suffix}")
