"""remove_user_id_from_non_patient_practitioner_resources

Revision ID: 33d766495d0f
Revises: b1ac97f80972
Create Date: 2026-10-31 12:06:19.192776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33d766495d0f'
down_revision: Union[str, None] = 'b1ac97f80972'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "activity_definition",
    "allergy_intolerance",
    "care_plan",
    "care_team",
    "condition",
    "consent",
    "diagnostic_report",
    "document_reference",
    "episode_of_care",
    "group",
    "medication_request",
    "observation",
    "observation_definition",
    "plan_definition",
    "procedure",
    "questionnaire",
    "questionnaire_response",
    "service_request",
    "specimen",
]


def upgrade() -> None:
    for table in TABLES:
        op.drop_index(op.f(f"ix_{table}_user_id"), table_name=table)
        op.drop_column(table, "user_id")


def downgrade() -> None:
    for table in reversed(TABLES):
        op.add_column(table, sa.Column("user_id", sa.String(), nullable=True))
        op.create_index(op.f(f"ix_{table}_user_id"), table, ["user_id"], unique=False)
