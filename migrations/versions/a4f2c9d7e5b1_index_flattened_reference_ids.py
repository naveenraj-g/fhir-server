"""index_flattened_reference_ids

Indexes every existing flattened cross-resource reference `_id` column
(provided_by_id, practitioner_id, organization_id, assigner_id, reference_id,
etc.) across the already-reworked resources, for consistency with
Slot.schedule_id, which was indexed from the start of its own (separate,
not-yet-applied) rework migration. These are plain, non-unique, purely
additive indexes — no data or nullability changes.

Revision ID: a4f2c9d7e5b1
Revises: 1827c7ee9967
Create Date: 2026-09-03 08:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a4f2c9d7e5b1'
down_revision: Union[str, None] = '1827c7ee9967'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_INDEXES = [
    ("ix_healthcare_service_provided_by_id", "healthcare_service", "provided_by_id"),
    ("ix_healthcare_service_coverage_area_reference_id", "healthcare_service_coverage_area", "reference_id"),
    ("ix_healthcare_service_endpoint_reference_id", "healthcare_service_endpoint", "reference_id"),
    ("ix_healthcare_service_identifier_assigner_id", "healthcare_service_identifier", "assigner_id"),
    ("ix_healthcare_service_location_reference_id", "healthcare_service_location", "reference_id"),
    ("ix_location_managing_organization_id", "location", "managing_organization_id"),
    ("ix_location_part_of_id", "location", "part_of_id"),
    ("ix_location_endpoint_reference_id", "location_endpoint", "reference_id"),
    ("ix_location_identifier_assigner_id", "location_identifier", "assigner_id"),
    ("ix_organization_partof_id", "organization", "partof_id"),
    ("ix_organization_endpoint_reference_id", "organization_endpoint", "reference_id"),
    ("ix_organization_identifier_assigner_id", "organization_identifier", "assigner_id"),
    ("ix_patient_managing_organization_id", "patient", "managing_organization_id"),
    ("ix_patient_contact_organization_id", "patient_contact", "organization_id"),
    ("ix_patient_general_practitioner_reference_id", "patient_general_practitioner", "reference_id"),
    ("ix_patient_identifier_assigner_id", "patient_identifier", "assigner_id"),
    ("ix_patient_link_other_id", "patient_link", "other_id"),
    ("ix_practitioner_identifier_assigner_id", "practitioner_identifier", "assigner_id"),
    ("ix_practitioner_qualification_issuer_id", "practitioner_qualification", "issuer_id"),
    ("ix_practitioner_qualification_identifier_assigner_id", "practitioner_qualification_identifier", "assigner_id"),
    ("ix_practitioner_role_organization_id", "practitioner_role", "organization_id"),
    ("ix_practitioner_role_practitioner_id", "practitioner_role", "practitioner_id"),
    ("ix_practitioner_role_endpoint_reference_id", "practitioner_role_endpoint", "reference_id"),
    ("ix_practitioner_role_healthcare_service_reference_id", "practitioner_role_healthcare_service", "reference_id"),
    ("ix_practitioner_role_identifier_assigner_id", "practitioner_role_identifier", "assigner_id"),
    ("ix_practitioner_role_location_reference_id", "practitioner_role_location", "reference_id"),
    ("ix_schedule_actor_reference_id", "schedule_actor", "reference_id"),
    ("ix_schedule_identifier_assigner_id", "schedule_identifier", "assigner_id"),
]


def upgrade() -> None:
    for index_name, table_name, column_name in _INDEXES:
        op.create_index(index_name, table_name, [column_name], unique=False)


def downgrade() -> None:
    for index_name, table_name, _column_name in reversed(_INDEXES):
        op.drop_index(index_name, table_name=table_name)
