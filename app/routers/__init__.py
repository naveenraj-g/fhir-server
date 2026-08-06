from fastapi import APIRouter

from .allergy_intolerance import router as allergy_intolerance_router
from .appointment import router as appointment_router
from .audit_event import router as audit_event_router
from .care_plan import router as care_plan_router
from .claim import router as claim_router
from .claim_response import router as claim_response_router
from .condition import router as condition_router
from .coverage import router as coverage_router
from .device_request import router as device_request_router
from .diagnostic_report import router as diagnostic_report_router
from .document_reference import router as document_reference_router
from .encounter import router as encounter_router
from .episode_of_care import router as episode_of_care_router
from .healthcare_service import router as healthcare_service_router
from .immunization import router as immunization_router
from .insurance_plan import router as insurance_plan_router
from .invoice import router as invoice_router
from .location import router as location_router
from .medication import router as medication_router
from .medication_request import router as medication_request_router
from .observation import router as observation_router
from .organization import router as organization_router
from .patient import router as patient_router
from .practitioner import router as practitioner_router
from .practitioner_role import router as practitioner_role_router
from .procedure import router as procedure_router
from .provenance import router as provenance_router
from .questionnaire_response import router as questionnaire_response_router
from .related_person import router as related_person_router
from .schedule import router as schedule_router
from .service_request import router as service_request_router
from .slot import router as slot_router
from .specimen import router as specimen_router
from .task import router as task_router

# Every resource router this server can mount, keyed by the name used in
# routes.yaml's `routes:` block. Every router is always imported (cheap, no
# side effects) — only *mounting* is conditional on routes.yaml, resolved at
# startup by build_api_router(). See CLAUDE.md's "Enabling/Disabling
# Resources" section.
_ROUTERS: dict[str, tuple[APIRouter, str, str]] = {
    "patient": (patient_router, "/patients", "Patients"),
    "practitioner": (practitioner_router, "/practitioners", "Practitioners"),
    "organization": (organization_router, "/organizations", "Organizations"),
    "encounter": (encounter_router, "/encounters", "Encounters"),
    "appointment": (appointment_router, "/appointments", "Appointments"),
    "questionnaire_response": (
        questionnaire_response_router,
        "/questionnaire-responses",
        "QuestionnaireResponses",
    ),
    "condition": (condition_router, "/conditions", "Conditions"),
    "service_request": (
        service_request_router,
        "/service-requests",
        "ServiceRequests",
    ),
    "device_request": (device_request_router, "/device-requests", "DeviceRequests"),
    "diagnostic_report": (
        diagnostic_report_router,
        "/diagnostic-reports",
        "DiagnosticReports",
    ),
    "medication_request": (
        medication_request_router,
        "/medication-requests",
        "MedicationRequests",
    ),
    "observation": (observation_router, "/observations", "Observations"),
    "procedure": (procedure_router, "/procedures", "Procedures"),
    "practitioner_role": (
        practitioner_role_router,
        "/practitioner-roles",
        "PractitionerRoles",
    ),
    "schedule": (schedule_router, "/schedules", "Schedules"),
    "slot": (slot_router, "/slots", "Slots"),
    "healthcare_service": (
        healthcare_service_router,
        "/healthcare-services",
        "HealthcareServices",
    ),
    "claim": (claim_router, "/claims", "Claims"),
    "claim_response": (claim_response_router, "/claim-responses", "ClaimResponses"),
    "invoice": (invoice_router, "/invoices", "Invoices"),
    "location": (location_router, "/locations", "Locations"),
    "coverage": (coverage_router, "/coverages", "Coverages"),
    "medication": (medication_router, "/medications", "Medications"),
    "allergy_intolerance": (
        allergy_intolerance_router,
        "/allergy-intolerances",
        "AllergyIntolerances",
    ),
    "provenance": (provenance_router, "/provenances", "Provenances"),
    "task": (task_router, "/tasks", "Tasks"),
    "care_plan": (care_plan_router, "/care-plans", "CarePlans"),
    "related_person": (
        related_person_router,
        "/related-persons",
        "RelatedPersons",
    ),
    "specimen": (specimen_router, "/specimens", "Specimens"),
    "document_reference": (
        document_reference_router,
        "/document-references",
        "DocumentReferences",
    ),
    "immunization": (immunization_router, "/immunizations", "Immunizations"),
    "audit_event": (audit_event_router, "/audit-events", "AuditEvents"),
    "episode_of_care": (
        episode_of_care_router,
        "/episode-of-cares",
        "EpisodeOfCares",
    ),
    "insurance_plan": (insurance_plan_router, "/insurance-plans", "InsurancePlans"),
}


def build_api_router(enabled: set[str]) -> APIRouter:
    """Builds the top-level API router, mounting only resources present in
    `enabled` (the set returned by app.core.routes_config.load_enabled_routes).
    Unknown names in `enabled` that aren't in _ROUTERS are silently ignored —
    routes.yaml listing a not-yet-implemented resource shouldn't crash startup."""
    api_router = APIRouter()
    for name, (router, prefix, tag) in _ROUTERS.items():
        if name in enabled:
            api_router.include_router(router, prefix=prefix, tags=[tag])
    return api_router
