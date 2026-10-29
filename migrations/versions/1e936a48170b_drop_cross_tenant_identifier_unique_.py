"""drop_cross_tenant_identifier_unique_constraints

FHIR R4 doesn't require identifier (system, value) uniqueness at all — it's
a local/profile decision, not a base-resource rule (see
app/models/organization/identifier.py's docstring, which already had this
right). A plain, ungated UniqueConstraint on these 8 identifier child tables
was a real cross-tenant bug: none of them were scoped to tenant_id or even
to the owning parent row, so two unrelated resources — in two different
orgs — could never share the same identifier value under the same system.
Drops the same constraint shape Organization/Practitioner never had.

Revision ID: 1e936a48170b
Revises: a681823da147
Create Date: 2026-10-29 21:03:31.797242

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e936a48170b'
down_revision: Union[str, None] = 'a681823da147'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_CONSTRAINTS = [
    ("appointment_identifier", "uq_appointment_identifier_system_value"),
    ("appointment_response_identifier", "uq_appointment_response_identifier_system_value"),
    ("encounter_identifier", "uq_encounter_identifier_system_value"),
    ("healthcare_service_identifier", "uq_healthcare_service_identifier_system_value"),
    ("location_identifier", "uq_location_identifier_system_value"),
    ("practitioner_role_identifier", "uq_practitioner_role_identifier_system_value"),
    ("schedule_identifier", "uq_schedule_identifier_system_value"),
    ("slot_identifier", "uq_slot_identifier_system_value"),
]


def upgrade() -> None:
    for table, name in _CONSTRAINTS:
        op.drop_constraint(name, table, type_="unique")


def downgrade() -> None:
    for table, name in _CONSTRAINTS:
        op.create_unique_constraint(name, table, ["system", "value"])
