"""drop_reference_list_dedup_unique_constraints

FHIR R4 never forbids a resource from listing the same reference twice in
one of its own 0..* Reference fields — that's a profile-layer invariant a
deployment can choose to add, never a base-resource rule. A plain
UniqueConstraint on (parent_pk, reference_type, reference_id) — or just
(parent_pk, reference_id) on the handful of tables with no reference_type
column — shipped on 43 reference-list child tables across DiagnosticReport,
Observation, MedicationRequest, ServiceRequest, QuestionnaireResponse,
Encounter, Appointment, Schedule, PractitionerRole, HealthcareService, and
Location. OrganizationEndpoint/OrganizationIdentifier/PractitionerIdentifier
already had the right shape (no constraint) the whole time — see their own
docstrings. Drops all 43 to match.

Revision ID: dc04b2b10995
Revises: 1e936a48170b
Create Date: 2026-10-29 21:21:25.373380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc04b2b10995'
down_revision: Union[str, None] = '1e936a48170b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, constraint_name, parent_pk_column) — reference_type + reference_id
# complete the column list.
_THREE_COL_CONSTRAINTS = [
    ("diagnostic_report_imaging_study", "uq_diagnostic_report_imaging_study_reference", "diagnostic_report_pk"),
    ("diagnostic_report_result", "uq_diagnostic_report_result_reference", "diagnostic_report_pk"),
    ("diagnostic_report_specimen", "uq_diagnostic_report_specimen_reference", "diagnostic_report_pk"),
    ("diagnostic_report_results_interpreter", "uq_diagnostic_report_results_interpreter_reference", "diagnostic_report_pk"),
    ("diagnostic_report_performer", "uq_diagnostic_report_performer_reference", "diagnostic_report_pk"),
    ("diagnostic_report_based_on", "uq_diagnostic_report_based_on_reference", "diagnostic_report_pk"),
    ("observation_derived_from", "uq_observation_derived_from_reference", "observation_pk"),
    ("observation_has_member", "uq_observation_has_member_reference", "observation_pk"),
    ("observation_performer", "uq_observation_performer_reference", "observation_pk"),
    ("observation_focus", "uq_observation_focus_reference", "observation_pk"),
    ("observation_part_of", "uq_observation_part_of_reference", "observation_pk"),
    ("observation_based_on", "uq_observation_based_on_reference", "observation_pk"),
    ("medication_request_insurance", "uq_medication_request_insurance_reference", "medication_request_pk"),
    ("medication_request_based_on", "uq_medication_request_based_on_reference", "medication_request_pk"),
    ("medication_request_reason_reference", "uq_medication_request_reason_reference_reference", "medication_request_pk"),
    ("service_request_performer", "uq_service_request_performer_reference", "service_request_pk"),
    ("service_request_insurance", "uq_service_request_insurance_reference", "service_request_pk"),
    ("service_request_reason_reference", "uq_service_request_reason_reference_reference", "service_request_pk"),
    ("service_request_based_on", "uq_service_request_based_on_reference", "service_request_pk"),
    ("questionnaire_response_part_of", "uq_questionnaire_response_part_of_reference", "questionnaire_response_pk"),
    ("questionnaire_response_based_on", "uq_questionnaire_response_based_on_reference", "questionnaire_response_pk"),
    ("encounter_account", "uq_encounter_account_reference", "encounter_pk"),
    ("encounter_reason_reference", "uq_encounter_reason_reference_reference", "encounter_pk"),
    ("encounter_appointment", "uq_encounter_appointment_reference", "encounter_pk"),
    ("encounter_based_on", "uq_encounter_based_on_reference", "encounter_pk"),
    ("encounter_episode_of_care", "uq_encounter_episode_of_care_reference", "encounter_pk"),
    ("appointment_based_on", "uq_appointment_based_on_reference", "appointment_pk"),
    ("appointment_slot", "uq_appointment_slot_reference", "appointment_pk"),
    ("appointment_reason_reference", "uq_appointment_reason_reference_reference", "appointment_pk"),
    ("schedule_actor", "uq_schedule_actor_reference", "schedule_pk"),
    ("practitioner_role_endpoint", "uq_practitioner_role_endpoint_reference", "practitioner_role_pk"),
    ("practitioner_role_healthcare_service", "uq_practitioner_role_healthcare_service_reference", "practitioner_role_pk"),
    ("practitioner_role_location", "uq_practitioner_role_location_reference", "practitioner_role_pk"),
    ("healthcare_service_endpoint", "uq_healthcare_service_endpoint_reference", "healthcare_service_pk"),
    ("healthcare_service_coverage_area", "uq_healthcare_service_coverage_area_reference", "healthcare_service_pk"),
    ("healthcare_service_location", "uq_healthcare_service_location_reference", "healthcare_service_pk"),
    ("location_endpoint", "uq_location_endpoint_reference", "location_pk"),
]

# (table, constraint_name, parent_pk_column) — no reference_type column on
# these particular tables, so the constraint was only ever (parent_pk,
# reference_id).
_TWO_COL_CONSTRAINTS = [
    ("medication_request_event_history", "uq_medication_request_event_history_reference", "medication_request_pk"),
    ("medication_request_detected_issue", "uq_medication_request_detected_issue_reference", "medication_request_pk"),
    ("service_request_relevant_history", "uq_service_request_relevant_history_reference", "service_request_pk"),
    ("service_request_specimen", "uq_service_request_specimen_reference", "service_request_pk"),
    ("service_request_location_reference", "uq_service_request_location_reference_reference", "service_request_pk"),
    ("service_request_replaces", "uq_service_request_replaces_reference", "service_request_pk"),
]


def upgrade() -> None:
    for table, name, _ in _THREE_COL_CONSTRAINTS:
        op.drop_constraint(name, table, type_="unique")
    for table, name, _ in _TWO_COL_CONSTRAINTS:
        op.drop_constraint(name, table, type_="unique")


def downgrade() -> None:
    for table, name, parent_pk in _THREE_COL_CONSTRAINTS:
        op.create_unique_constraint(name, table, [parent_pk, "reference_type", "reference_id"])
    for table, name, parent_pk in _TWO_COL_CONSTRAINTS:
        op.create_unique_constraint(name, table, [parent_pk, "reference_id"])
