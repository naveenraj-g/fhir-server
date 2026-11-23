"""One minimal, valid create body per rebuilt resource - the table the generic reference-check
tests run over.

Adding a resource to the server means adding a row here: `test_every_checkable_type_has_a_case`
fails until it has one, so a new resource cannot ship without being covered by the generic
dangling-reference test.

Each entry is (route, async factory(client) -> body). Most bodies point their required references
at absolute URLs (not existence-checked); the few that need a real row (a Slot's Schedule) create it.
"""

import re

from tests.integration.allergy_intolerance.support import allergy_body
from tests.integration.appointment.support import appointment_body
from tests.integration.appointment_response.support import response_body
from tests.integration.care_plan.support import care_plan_body
from tests.integration.care_team.support import care_team_body
from tests.integration.clinical_impression.support import impression_body
from tests.integration.condition.support import condition_body
from tests.integration.detected_issue.support import issue_body
from tests.integration.diagnostic_report.support import report_body
from tests.integration.document_reference.support import document_body
from tests.integration.encounter.support import encounter_body
from tests.integration.episode_of_care.support import episode_body
from tests.integration.endpoint.support import MINIMAL as ENDPOINT
from tests.integration.family_member_history.support import history_body
from tests.integration.group.support import group_body
from tests.integration.healthcare_service.support import MINIMAL as HEALTHCARE_SERVICE
from tests.integration.immunization.support import immunization_body
from tests.integration.immunization_evaluation.support import evaluation_body
from tests.integration.immunization_recommendation.support import recommendation_body
from tests.integration.location.support import MINIMAL as LOCATION
from tests.integration.medication.support import medication_body
from tests.integration.medication_request.support import medication_request_body
from tests.integration.observation.support import observation_body
from tests.integration.organization.support import MINIMAL as ORGANIZATION
from tests.integration.patient.support import MINIMAL as PATIENT
from tests.integration.practitioner.support import MINIMAL as PRACTITIONER
from tests.integration.practitioner_role.support import MINIMAL as PRACTITIONER_ROLE
from tests.integration.procedure.support import procedure_body
from tests.integration.medication_administration.support import (
    medication_administration_body,
)
from tests.integration.medication_statement.support import (
    medication_statement_body,
)
from tests.integration.questionnaire_response.support import questionnaire_response_body
from tests.integration.related_person.support import related_person_body
from tests.integration.risk_assessment.support import assessment_body
from tests.integration.schedule.support import create_schedule
from tests.integration.service_request.support import service_request_body
from tests.integration.slot.support import slot_body
from tests.integration.specimen.support import specimen_body

API = "/api/fhir/v1"
EXTERNAL_ACTOR = {"reference": "https://other.example.org/fhir/Patient/1"}


def _fixed(body):
    async def make(client):
        return dict(body() if callable(body) else body)

    return make


async def _slot(client):
    return slot_body(await create_schedule(client))


CASES = {
    "AllergyIntolerance": (f"{API}/allergy-intolerances", _fixed(allergy_body)),
    "Appointment": (f"{API}/appointments", _fixed(appointment_body)),
    "AppointmentResponse": (f"{API}/appointment-responses", _fixed(response_body)),
    "CarePlan": (f"{API}/care-plans", _fixed(care_plan_body)),
    "CareTeam": (f"{API}/care-teams", _fixed(care_team_body)),
    "ClinicalImpression": (f"{API}/clinical-impressions", _fixed(impression_body)),
    "Condition": (f"{API}/conditions", _fixed(condition_body)),
    "DetectedIssue": (f"{API}/detected-issues", _fixed(issue_body)),
    "DiagnosticReport": (f"{API}/diagnostic-reports", _fixed(report_body)),
    "DocumentReference": (f"{API}/document-references", _fixed(document_body)),
    "Encounter": (f"{API}/encounters", _fixed(encounter_body)),
    "Endpoint": (f"{API}/endpoints", _fixed(ENDPOINT)),
    "EpisodeOfCare": (f"{API}/episodes-of-care", _fixed(episode_body)),
    "FamilyMemberHistory": (f"{API}/family-member-histories", _fixed(history_body)),
    "Group": (f"{API}/groups", _fixed(group_body)),
    "HealthcareService": (f"{API}/healthcare-services", _fixed(HEALTHCARE_SERVICE)),
    "Immunization": (f"{API}/immunizations", _fixed(immunization_body)),
    "ImmunizationEvaluation": (
        f"{API}/immunization-evaluations",
        _fixed(evaluation_body),
    ),
    "ImmunizationRecommendation": (
        f"{API}/immunization-recommendations",
        _fixed(recommendation_body),
    ),
    "Location": (f"{API}/locations", _fixed(LOCATION)),
    "Medication": (f"{API}/medications", _fixed(medication_body)),
    "MedicationRequest": (
        f"{API}/medication-requests",
        _fixed(medication_request_body),
    ),
    "Observation": (f"{API}/observations", _fixed(observation_body)),
    "Organization": (f"{API}/organizations", _fixed(ORGANIZATION)),
    "Patient": (f"{API}/patients", _fixed(PATIENT)),
    "Practitioner": (f"{API}/practitioners", _fixed(PRACTITIONER)),
    "PractitionerRole": (f"{API}/practitioner-roles", _fixed(PRACTITIONER_ROLE)),
    "Procedure": (f"{API}/procedures", _fixed(procedure_body)),
    "Questionnaire": (f"{API}/questionnaires", _fixed({"status": "draft"})),
    "MedicationAdministration": (
        f"{API}/medication-administrations",
        _fixed(medication_administration_body),
    ),
    "MedicationStatement": (
        f"{API}/medication-statements",
        _fixed(medication_statement_body),
    ),
    "QuestionnaireResponse": (
        f"{API}/questionnaire-responses",
        _fixed(questionnaire_response_body),
    ),
    "RelatedPerson": (f"{API}/related-persons", _fixed(related_person_body)),
    "RiskAssessment": (f"{API}/risk-assessments", _fixed(assessment_body)),
    "Schedule": (
        f"{API}/schedules",
        _fixed({"active": True, "actor": [EXTERNAL_ACTOR]}),
    ),
    "ServiceRequest": (f"{API}/service-requests", _fixed(service_request_body)),
    "Slot": (f"{API}/slots", _slot),
    "Specimen": (f"{API}/specimens", _fixed(specimen_body)),
}


def permission_name(resource_type: str) -> str:
    """`CarePlan` -> `care_plan` (the RBAC resource name)."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", resource_type).lower()
