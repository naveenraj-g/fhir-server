"""drop legacy practitioner practitioner_role and patient_general_practitioner objects

Revision ID: eca50d0f7023
Revises: 6b9ea4655c7d
Create Date: 2026-10-22 20:12:49.714700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eca50d0f7023'
down_revision: Union[str, None] = '6b9ea4655c7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


"""The Python model files for Practitioner, PractitionerRole, and Patient
were all deleted in an earlier mass resource cleanup (see CLAUDE.md's
current resource list), but that cleanup only removed source files — it
never ran a matching `alembic downgrade`, so the old tables/types/sequences
these three resources had created stayed live in the database, built
against the pre-rework conventions (flattened six-column CodeableConcept,
no TenantAuditMixin, etc.). Practitioner is being rebuilt from scratch
against the current conventions (see migration that follows this one), so
its old objects need to go first rather than have autogenerate try to diff
new TenantAuditMixin-based models against stale legacy tables.

PractitionerRole and `patient_general_practitioner` (Patient's own
`generalPractitioner` reference table) are dropped here too even though
neither is being rebuilt today, at the user's explicit request, since both
are themselves orphaned the same way and would hit the same problem
whenever they're rebuilt. The rest of Patient's tables are deliberately
left untouched — Patient itself isn't being rebuilt today and wasn't part
of this cleanup's scope.

Shared enum types reused elsewhere (`administrative_gender`, `human_name_use`,
`identifier_use`, `organization_reference_type`, `address_use`, `address_type`,
`contact_point_system`, `contact_point_use`) are NOT dropped — Organization/
Location/HealthcareService (and Patient's own remaining tables) still use them.

No reasonable downgrade: recreating 20 obsolete tables nothing will ever
read from again isn't worth the code — this is a one-way cleanup.
"""


def upgrade() -> None:
    # Children before parents, though CASCADE below makes the exact order
    # defensive rather than load-bearing.
    for table in [
        "patient_general_practitioner",
        "practitioner_qualification_identifier_type_coding",
        "practitioner_qualification_identifier",
        "practitioner_qualification",
        "practitioner_address",
        "practitioner_communication",
        "practitioner_identifier",
        "practitioner_name",
        "practitioner_photo",
        "practitioner_telecom",
        "practitioner",
        "practitioner_role_available_time",
        "practitioner_role_not_available",
        "practitioner_role_code",
        "practitioner_role_endpoint",
        "practitioner_role_healthcare_service",
        "practitioner_role_identifier",
        "practitioner_role_location",
        "practitioner_role_specialty",
        "practitioner_role_telecom",
        "practitioner_role",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    for enum_type in [
        "patient_gp_type",
        "practitioner_role_endpoint_reference_type",
        "practitioner_role_healthcare_service_reference_type",
        "practitioner_role_location_reference_type",
        "practitioner_role_practitioner_reference_type",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_type}")

    for seq in [
        "patient_general_practitioner_id_seq",
        "practitioner_address_id_seq",
        "practitioner_communication_id_seq",
        "practitioner_id_seq",
        "practitioner_identifier_id_seq",
        "practitioner_name_id_seq",
        "practitioner_photo_id_seq",
        "practitioner_pub_seq",
        "practitioner_qualification_id_seq",
        "practitioner_qualification_identifier_id_seq",
        "practitioner_role_available_time_id_seq",
        "practitioner_role_code_id_seq",
        "practitioner_role_endpoint_id_seq",
        "practitioner_role_healthcare_service_id_seq",
        "practitioner_role_id_seq",
        "practitioner_role_identifier_id_seq",
        "practitioner_role_location_id_seq",
        "practitioner_role_not_available_id_seq",
        "practitioner_role_pub_seq",
        "practitioner_role_specialty_id_seq",
        "practitioner_role_telecom_id_seq",
        "practitioner_telecom_id_seq",
    ]:
        op.execute(f"DROP SEQUENCE IF EXISTS {seq}")


def downgrade() -> None:
    pass
