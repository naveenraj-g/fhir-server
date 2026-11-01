"""add_communication_request_reference_identifier_columns

Revision ID: 3b7a128e49c1
Revises: 2187525ad268
Create Date: 2026-11-01 12:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3b7a128e49c1'
down_revision: Union[str, None] = '2187525ad268'
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
    # 1. Main communication_request table: group_identifier_assigner, subject, encounter, requester, sender
    for prefix in ("group_identifier_assigner", "subject", "encounter", "requester", "sender"):
        for suffix, col_type in _IDENTIFIER_COLS:
            op.add_column("communication_request", sa.Column(f"{prefix}_{suffix}", col_type, nullable=True))

    # 2. Reference list tables: based_on, replaces, about, recipient, reason_reference
    ref_tables = [
        "communication_request_based_on",
        "communication_request_replaces",
        "communication_request_about",
        "communication_request_recipient",
        "communication_request_reason_reference",
    ]
    for table in ref_tables:
        for suffix, col_type in _IDENTIFIER_COLS:
            op.add_column(table, sa.Column(f"reference_{suffix}", col_type, nullable=True))

    # 3. Payload table: content_reference
    for suffix, col_type in _IDENTIFIER_COLS:
        op.add_column("communication_request_payload", sa.Column(f"content_reference_{suffix}", col_type, nullable=True))

    # 4. Note table: author
    for suffix, col_type in _IDENTIFIER_COLS:
        op.add_column("communication_request_note", sa.Column(f"author_{suffix}", col_type, nullable=True))


def downgrade() -> None:
    # 4. Note table: author
    for suffix, _ in reversed(_IDENTIFIER_COLS):
        op.drop_column("communication_request_note", f"author_{suffix}")

    # 3. Payload table: content_reference
    for suffix, _ in reversed(_IDENTIFIER_COLS):
        op.drop_column("communication_request_payload", f"content_reference_{suffix}")

    # 2. Reference list tables
    ref_tables = [
        "communication_request_reason_reference",
        "communication_request_recipient",
        "communication_request_about",
        "communication_request_replaces",
        "communication_request_based_on",
    ]
    for table in ref_tables:
        for suffix, _ in reversed(_IDENTIFIER_COLS):
            op.drop_column(table, f"reference_{suffix}")

    # 1. Main communication_request table
    for prefix in reversed(("group_identifier_assigner", "subject", "encounter", "requester", "sender")):
        for suffix, _ in reversed(_IDENTIFIER_COLS):
            op.drop_column("communication_request", f"{prefix}_{suffix}")
