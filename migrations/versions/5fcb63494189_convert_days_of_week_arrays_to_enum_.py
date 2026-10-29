"""convert_days_of_week_arrays_to_enum_backed_columns

daysOfWeek (Location.hoursOfOperation, HealthcareService.availableTime,
PractitionerRole.availableTime) carries a FHIR R4 `required` binding — a
closed code list HL7 defines completely (mon|tue|wed|thu|fri|sat|sun), with
no room for a deployment/profile to extend it. Unlike a genuinely free-form
0..* scalar list (Address.line, HumanName.given/prefix/suffix), this one's
value set is fully known up front, so it gets a real Postgres ARRAY(ENUM)
column instead of ARRAY(VARCHAR) — the same way every single-value FHIR
code column in this codebase already does (LocationModel.status/.mode,
etc.). Existing values are already schema-validated against this exact
list at every write path, so a straight cast is safe — no data cleanup
needed.

Revision ID: 5fcb63494189
Revises: dc04b2b10995
Create Date: 2026-10-29 21:23:39.542020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5fcb63494189'
down_revision: Union[str, None] = 'dc04b2b10995'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_DAYS = "'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'"

_TABLES = [
    ("location_hours_of_operation", "location_day_of_week"),
    ("healthcare_service_available_time", "healthcare_service_day_of_week"),
    ("practitioner_role_available_time", "practitioner_role_day_of_week"),
]


def upgrade() -> None:
    for table, enum_name in _TABLES:
        op.execute(f"CREATE TYPE {enum_name} AS ENUM ({_DAYS})")
        op.execute(
            f"""
            ALTER TABLE {table}
            ALTER COLUMN days_of_week TYPE {enum_name}[]
            USING days_of_week::text[]::{enum_name}[]
            """
        )


def downgrade() -> None:
    for table, enum_name in _TABLES:
        op.execute(
            f"""
            ALTER TABLE {table}
            ALTER COLUMN days_of_week TYPE varchar[]
            USING days_of_week::text[]::varchar[]
            """
        )
        op.execute(f"DROP TYPE {enum_name}")
