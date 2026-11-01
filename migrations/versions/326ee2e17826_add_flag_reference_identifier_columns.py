"""add_flag_reference_identifier_columns

Revision ID: 326ee2e17826
Revises: 8af4876fdea2
Create Date: 2026-11-01 14:08:44.799167

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '326ee2e17826'
down_revision: Union[str, None] = '8af4876fdea2'
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
    op.alter_column("flag", "subject_reference", existing_type=sa.String(), nullable=True)
    op.alter_column(
        "flag",
        "subject_type",
        existing_type=sa.Enum(
            "Patient",
            "Location",
            "Group",
            "Organization",
            "Practitioner",
            "PlanDefinition",
            "Medication",
            "Procedure",
            name="flag_subject_reference_type",
        ),
        nullable=True,
    )

    for prefix in ("subject", "encounter", "author"):
        for suffix, col_type in _IDENTIFIER_COLS:
            op.add_column("flag", sa.Column(f"{prefix}_{suffix}", col_type, nullable=True))


def downgrade() -> None:
    for prefix in reversed(("subject", "encounter", "author")):
        for suffix, _ in reversed(_IDENTIFIER_COLS):
            op.drop_column("flag", f"{prefix}_{suffix}")

    op.alter_column(
        "flag",
        "subject_type",
        existing_type=sa.Enum(
            "Patient",
            "Location",
            "Group",
            "Organization",
            "Practitioner",
            "PlanDefinition",
            "Medication",
            "Procedure",
            name="flag_subject_reference_type",
        ),
        nullable=False,
    )
    op.alter_column("flag", "subject_reference", existing_type=sa.String(), nullable=False)
