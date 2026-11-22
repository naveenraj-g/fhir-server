"""align the indexes of the older rebuilt resources with their models

Revision ID: b3f9a6c2d741
Revises: a1d7e4f0b826
Create Date: 2026-12-15 13:00:00.000000

`alembic check` on a database built from the migrations shows a few indexes that the models declare
(`index=True`, the shared audit columns) but that the early content-based rebuild migrations never
created, plus a unique constraint on `patient.patient_id` that the model does not declare (the public
id's uniqueness is the unique index). Later rebuilds create all of these (see Specimen's migration);
this brings the older ones in line:

  allergy_intolerance: id
  condition:           tenant_id, created_at, updated_at
  family_member_history: id
  related_person:      id, tenant_id, created_at, updated_at, patient_id, related_person_id (unique)
  risk_assessment:     id
  patient:             drops the constraint `patient_patient_id_key`; keeps a unique index on patient_id

downgrade: not supported (one-way, like the other content-based migrations).
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3f9a6c2d741"
down_revision: Union[str, None] = "a1d7e4f0b826"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table, column, unique)
_INDEXES = (
    ("allergy_intolerance", "id", False),
    ("condition", "tenant_id", False),
    ("condition", "created_at", False),
    ("condition", "updated_at", False),
    ("family_member_history", "id", False),
    ("related_person", "id", False),
    ("related_person", "tenant_id", False),
    ("related_person", "created_at", False),
    ("related_person", "updated_at", False),
    ("related_person", "patient_id", False),
    ("related_person", "related_person_id", True),
    ("risk_assessment", "id", False),
)


def upgrade() -> None:
    for table, column, unique in _INDEXES:
        op.create_index(
            f"ix_{table}_{column}", table, [column], unique=unique, if_not_exists=True
        )
    # the public id stays unique through the unique index, not a separate constraint
    op.create_index(
        "ix_patient_patient_id",
        "patient",
        ["patient_id"],
        unique=True,
        if_not_exists=True,
    )
    op.execute("ALTER TABLE patient DROP CONSTRAINT IF EXISTS patient_patient_id_key")


def downgrade() -> None:
    raise NotImplementedError(
        "index alignment migration is one-way. Restore from a backup taken before upgrading."
    )
