"""add_communication_reference_identifier_columns

Revision ID: 2187525ad268
Revises: cd0541a6d680
Create Date: 2026-11-01 12:09:31.700182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2187525ad268'
down_revision: Union[str, None] = 'cd0541a6d680'
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
    # 1. Main communication table: subject, encounter, sender
    for prefix in ("subject", "encounter", "sender"):
        for suffix, col_type in _IDENTIFIER_COLS:
            op.add_column("communication", sa.Column(f"{prefix}_{suffix}", col_type, nullable=True))

    # 2. Reference list tables: based_on, part_of, in_response_to, about, recipient, reason_reference
    ref_tables = [
        "communication_based_on",
        "communication_part_of",
        "communication_in_response_to",
        "communication_about",
        "communication_recipient",
        "communication_reason_reference",
    ]
    for table in ref_tables:
        for suffix, col_type in _IDENTIFIER_COLS:
            op.add_column(table, sa.Column(f"reference_{suffix}", col_type, nullable=True))

    # 3. Payload table: content_reference
    for suffix, col_type in _IDENTIFIER_COLS:
        op.add_column("communication_payload", sa.Column(f"content_reference_{suffix}", col_type, nullable=True))

    # 4. Note table: author
    for suffix, col_type in _IDENTIFIER_COLS:
        op.add_column("communication_note", sa.Column(f"author_{suffix}", col_type, nullable=True))


def downgrade() -> None:
    # 4. Note table: author
    for suffix, _ in reversed(_IDENTIFIER_COLS):
        op.drop_column("communication_note", f"author_{suffix}")

    # 3. Payload table: content_reference
    for suffix, _ in reversed(_IDENTIFIER_COLS):
        op.drop_column("communication_payload", f"content_reference_{suffix}")

    # 2. Reference list tables
    ref_tables = [
        "communication_reason_reference",
        "communication_recipient",
        "communication_about",
        "communication_in_response_to",
        "communication_part_of",
        "communication_based_on",
    ]
    for table in ref_tables:
        for suffix, _ in reversed(_IDENTIFIER_COLS):
            op.drop_column(table, f"reference_{suffix}")

    # 1. Main communication table
    for prefix in reversed(("subject", "encounter", "sender")):
        for suffix, _ in reversed(_IDENTIFIER_COLS):
            op.drop_column("communication", f"{prefix}_{suffix}")
