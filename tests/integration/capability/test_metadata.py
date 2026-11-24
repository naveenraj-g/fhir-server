"""GET /api/fhir/v1/metadata — the generated CapabilityStatement."""

import pytest

from app.core.config import settings
from app.repository.endpoint.search import endpoint_search
from app.repository.healthcare_service.search import healthcare_service_search
from app.repository.appointment.search import appointment_search
from app.repository.appointment_response.search import appointment_response_search
from app.repository.encounter.search import encounter_search
from app.repository.allergy_intolerance.search import allergy_intolerance_search
from app.repository.clinical_impression.search import clinical_impression_search
from app.repository.condition.search import condition_search
from app.repository.detected_issue.search import detected_issue_search
from app.repository.diagnostic_report.search import diagnostic_report_search
from app.repository.family_member_history.search import family_member_history_search
from app.repository.immunization.search import immunization_search
from app.repository.risk_assessment.search import risk_assessment_search
from app.repository.immunization_evaluation.search import immunization_evaluation_search
from app.repository.immunization_recommendation.search import (
    immunization_recommendation_search,
)
from app.repository.observation.search import observation_search
from app.repository.procedure.search import procedure_search
from app.repository.related_person.search import related_person_search
from app.repository.location.search import location_search
from app.repository.organization.search import organization_search
from app.repository.patient.search import patient_search
from app.repository.practitioner_role.search import practitioner_role_search
from app.repository.schedule.search import schedule_search
from app.repository.care_plan.search import care_plan_search
from app.repository.care_team.search import care_team_search
from app.repository.document_reference.search import document_reference_search
from app.repository.episode_of_care.search import episode_of_care_search
from app.repository.medication_administration.search import (
    medication_administration_search,
)
from app.repository.medication_dispense.search import (
    medication_dispense_search,
)
from app.repository.medication_knowledge.search import medication_knowledge_search
from app.repository.medication_statement.search import medication_statement_search
from app.repository.questionnaire.search import questionnaire_search
from app.repository.questionnaire_response.search import questionnaire_response_search
from app.repository.group.search import group_search
from app.repository.medication.search import medication_search
from app.repository.medication_request.search import medication_request_search
from app.repository.service_request.search import service_request_search
from app.repository.slot.search import slot_search
from app.repository.specimen.search import specimen_search
from app.repository.practitioner.search import practitioner_search

URL = "/api/fhir/v1/metadata"


async def _statement(client) -> dict:
    r = await client.get(URL)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/fhir+json")
    return r.json()


async def test_statement_basics(client):
    cs = await _statement(client)
    assert cs["resourceType"] == "CapabilityStatement"
    assert cs["fhirVersion"] == "4.0.1"
    assert cs["kind"] == "instance"
    assert cs["status"] == "active"
    assert cs["rest"][0]["mode"] == "server"


async def test_search_params_match_registries(client):
    cs = await _statement(client)
    by_type = {r["type"]: r for r in cs["rest"][0]["resource"]}
    expected = {
        "organization": ("Organization", organization_search()),
        "location": ("Location", location_search()),
        "practitioner": ("Practitioner", practitioner_search()),
        "healthcare_service": ("HealthcareService", healthcare_service_search()),
        "endpoint": ("Endpoint", endpoint_search()),
        "practitioner_role": ("PractitionerRole", practitioner_role_search()),
        "schedule": ("Schedule", schedule_search()),
        "care_plan": ("CarePlan", care_plan_search()),
        "care_team": ("CareTeam", care_team_search()),
        "document_reference": ("DocumentReference", document_reference_search()),
        "episode_of_care": ("EpisodeOfCare", episode_of_care_search()),
        "medication_administration": (
            "MedicationAdministration",
            medication_administration_search(),
        ),
        "medication_dispense": (
            "MedicationDispense",
            medication_dispense_search(),
        ),
        "medication_knowledge": (
            "MedicationKnowledge",
            medication_knowledge_search(),
        ),
        "medication_statement": ("MedicationStatement", medication_statement_search()),
        "questionnaire": ("Questionnaire", questionnaire_search()),
        "questionnaire_response": (
            "QuestionnaireResponse",
            questionnaire_response_search(),
        ),
        "group": ("Group", group_search()),
        "medication": ("Medication", medication_search()),
        "medication_request": ("MedicationRequest", medication_request_search()),
        "service_request": ("ServiceRequest", service_request_search()),
        "slot": ("Slot", slot_search()),
        "specimen": ("Specimen", specimen_search()),
        "patient": ("Patient", patient_search()),
        "appointment": ("Appointment", appointment_search()),
        "appointment_response": ("AppointmentResponse", appointment_response_search()),
        "encounter": ("Encounter", encounter_search()),
        "related_person": ("RelatedPerson", related_person_search()),
        "allergy_intolerance": ("AllergyIntolerance", allergy_intolerance_search()),
        "clinical_impression": ("ClinicalImpression", clinical_impression_search()),
        "condition": ("Condition", condition_search()),
        "detected_issue": ("DetectedIssue", detected_issue_search()),
        "diagnostic_report": ("DiagnosticReport", diagnostic_report_search()),
        "family_member_history": (
            "FamilyMemberHistory",
            family_member_history_search(),
        ),
        "immunization": ("Immunization", immunization_search()),
        "risk_assessment": ("RiskAssessment", risk_assessment_search()),
        "immunization_evaluation": (
            "ImmunizationEvaluation",
            immunization_evaluation_search(),
        ),
        "immunization_recommendation": (
            "ImmunizationRecommendation",
            immunization_recommendation_search(),
        ),
        "observation": ("Observation", observation_search()),
        "procedure": ("Procedure", procedure_search()),
    }
    enabled = {k: v for k, v in expected.items() if k in settings.routes.enabled}
    assert set(by_type) == {t for t, _ in enabled.values()}  # only what is mounted
    for rtype, registry in enabled.values():
        entry = by_type[rtype]
        assert {p["name"] for p in entry["searchParam"]} == set(registry.params)
        assert {"read", "create", "patch", "delete", "search-type"} == {
            i["code"] for i in entry["interaction"]
        }


async def test_includes_and_param_types(client):
    cs = await _statement(client)
    by_type = {r["type"]: r for r in cs["rest"][0]["resource"]}
    assert "Organization:partof" in by_type["Organization"]["searchInclude"]
    assert "Location:organization" in by_type["Organization"]["searchRevInclude"]
    if "location" not in settings.routes.enabled:
        pytest.skip("location router not enabled in configs/config.yaml")
    loc = {p["name"]: p for p in by_type["Location"]["searchParam"]}
    assert loc["near"]["type"] == "special"
    assert loc["_id"]["definition"] == "http://hl7.org/fhir/SearchParameter/Resource-id"
    assert loc["address-city"]["definition"].endswith("/Location-address-city")
