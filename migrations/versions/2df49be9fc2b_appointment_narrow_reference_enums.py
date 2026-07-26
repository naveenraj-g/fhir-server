"""appointment_narrow_reference_enums

Revision ID: 2df49be9fc2b
Revises: b9af7ac9b9ce
Create Date: 2026-07-26 16:05:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '2df49be9fc2b'
down_revision: Union[str, None] = 'b9af7ac9b9ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # appointment_based_on_reference_type: R5 allowed 7 target types incl.
    # RequestOrchestration; R4 basedOn only allows Reference(ServiceRequest).
    # Autogenerate doesn't diff enum value sets (only type names), so this
    # narrowing has to be done by hand via the rename-swap technique.
    op.execute('ALTER TYPE appointment_based_on_reference_type RENAME TO appointment_based_on_reference_type_old')
    op.execute("CREATE TYPE appointment_based_on_reference_type AS ENUM ('ServiceRequest')")
    op.execute(
        'ALTER TABLE appointment_based_on ALTER COLUMN reference_type '
        'TYPE appointment_based_on_reference_type '
        'USING reference_type::text::appointment_based_on_reference_type'
    )
    op.execute('DROP TYPE appointment_based_on_reference_type_old')

    # appointment_participant_actor_type: R5 added Group/CareTeam as allowed
    # participant.actor target types; R4 only allows the original 7.
    op.execute('ALTER TYPE appointment_participant_actor_type RENAME TO appointment_participant_actor_type_old')
    op.execute(
        "CREATE TYPE appointment_participant_actor_type AS ENUM "
        "('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Device', 'HealthcareService', 'Location')"
    )
    op.execute(
        'ALTER TABLE appointment_participant ALTER COLUMN reference_type '
        'TYPE appointment_participant_actor_type '
        'USING reference_type::text::appointment_participant_actor_type'
    )
    op.execute('DROP TYPE appointment_participant_actor_type_old')


def downgrade() -> None:
    op.execute('ALTER TYPE appointment_participant_actor_type RENAME TO appointment_participant_actor_type_new')
    op.execute(
        "CREATE TYPE appointment_participant_actor_type AS ENUM "
        "('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Device', 'HealthcareService', 'Location', 'Group', 'CareTeam')"
    )
    op.execute(
        'ALTER TABLE appointment_participant ALTER COLUMN reference_type '
        'TYPE appointment_participant_actor_type '
        'USING reference_type::text::appointment_participant_actor_type'
    )
    op.execute('DROP TYPE appointment_participant_actor_type_new')

    op.execute('ALTER TYPE appointment_based_on_reference_type RENAME TO appointment_based_on_reference_type_new')
    op.execute(
        "CREATE TYPE appointment_based_on_reference_type AS ENUM "
        "('CarePlan', 'DeviceRequest', 'MedicationRequest', 'ServiceRequest', 'RequestOrchestration', 'NutritionOrder', 'VisionPrescription')"
    )
    op.execute(
        'ALTER TABLE appointment_based_on ALTER COLUMN reference_type '
        'TYPE appointment_based_on_reference_type '
        'USING reference_type::text::appointment_based_on_reference_type'
    )
    op.execute('DROP TYPE appointment_based_on_reference_type_new')
