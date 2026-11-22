"""reference `*_type` index columns of the rebuilt resources: Postgres enum -> plain string

Revision ID: f9e4a1c7d583
Revises: e8d3f0b6c472
Create Date: 2026-12-15 10:00:00.000000

Every rebuilt (content-based) resource stores the resolved type of a relative `Type/<id>` reference
as a plain string, like Observation, ServiceRequest, CarePlan, ... The seven older rebuilds still
held it in a Postgres enum, one per field or shared with the not-yet-rebuilt resources:

  endpoint.managing_organization_type, healthcare_service.provided_by_type,
  location.managing_organization_type, location.part_of_type, location_endpoint.reference_type,
  organization.partof_type, organization_endpoint.reference_type,
  patient.managing_organization_type, practitioner_role.practitioner_type,
  practitioner_role.organization_type, slot.schedule_type

The enum protected nothing: the resource lives in `content`, and the indexer only fills these columns
with a type its element accepts. What a reference may point at is decided once per element in code
(the allowed-type tuples), and whether the target exists by the shared write-time reference check.

Each column becomes `varchar` (the labels were the type names, so `::text` keeps every value). An enum
type that no column uses any more is dropped; `organization_reference_type`, `practitioner_reference_type`
and the like stay for as long as a not-yet-rebuilt resource still uses them.

downgrade: not supported (one-way, like the other content-based migrations).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f9e4a1c7d583"
down_revision: Union[str, None] = "e8d3f0b6c472"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table, column, enum type the column used)
_COLUMNS = (
    ("endpoint", "managing_organization_type", "organization_reference_type"),
    ("healthcare_service", "provided_by_type", "organization_reference_type"),
    ("location", "managing_organization_type", "organization_reference_type"),
    ("location", "part_of_type", "location_part_of_reference_type"),
    ("location_endpoint", "reference_type", "location_endpoint_reference_type"),
    ("organization", "partof_type", "organization_reference_type"),
    ("organization_endpoint", "reference_type", "organization_endpoint_ref_type"),
    ("patient", "managing_organization_type", "organization_reference_type"),
    ("practitioner_role", "practitioner_type", "practitioner_reference_type"),
    ("practitioner_role", "organization_type", "organization_reference_type"),
    ("slot", "schedule_type", "schedule_reference_type"),
)


def upgrade() -> None:
    bind = op.get_bind()
    for table, column, _enum in _COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.String(),
            existing_nullable=True,
            postgresql_using=f"{column}::text",
        )
    # an enum type nothing uses any more (a column in any table, in any schema) goes
    for enum in sorted({e for _t, _c, e in _COLUMNS}):
        in_use = bind.execute(
            sa.text(
                "SELECT 1 FROM pg_attribute a JOIN pg_type t ON a.atttypid = t.oid "
                "WHERE t.typname = :name AND a.attnum > 0 AND NOT a.attisdropped LIMIT 1"
            ),
            {"name": enum},
        ).first()
        if not in_use:
            op.execute(f'DROP TYPE IF EXISTS "{enum}"')


def downgrade() -> None:
    raise NotImplementedError(
        "reference-type columns migration is one-way: the plain-string columns are not turned "
        "back into enums. Restore from a backup taken before upgrading."
    )
