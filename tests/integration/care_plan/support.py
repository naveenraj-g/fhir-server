"""Shared helpers and payloads for care_plan integration tests.

Request bodies are genuine FHIR R4 CarePlan JSON (camelCase, nested datatypes), and every
response is FHIR R4 too."""

# The resources a CarePlan points at (and that point back at it) are created through their own
# routers.
from tests.integration.appointment.support import (  # noqa: F401
    appointment_body,
    create_appointment,
)
from tests.integration.care_team.support import (  # noqa: F401
    care_team_body,
    create_care_team,
)
from tests.integration.condition.support import (  # noqa: F401
    condition_body,
    create_condition,
)
from tests.integration.encounter.support import (  # noqa: F401
    create_encounter,
    encounter_body,
)
from tests.integration.group.support import create_group, group_body  # noqa: F401
from tests.integration.medication.support import (  # noqa: F401
    create_medication,
    medication_body,
)
from tests.integration.medication_request.support import (  # noqa: F401
    create_medication_request,
    medication_request_body,
)
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_healthcare_service,
    create_location,
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)
from tests.integration.related_person.support import (  # noqa: F401
    create_related_person,
    related_person_body,
)
from tests.integration.service_request.support import (  # noqa: F401
    create_service_request,
    service_request_body,
)

BASE = "/api/fhir/v1/care-plans"
API = "/api/fhir/v1"

CARE_PLAN_IDS = "https://fhir-server.dev/fhir/identifier-system/care-plan-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
SCT = "http://snomed.info/sct"
LOINC = "http://loinc.org"
CATEGORY = "http://hl7.org/fhir/us/core/CodeSystem/careplan-category"


def concept(system: str, code: str, display: str | None = None) -> dict:
    return {
        "coding": [
            {
                "system": system,
                "code": code,
                **({"display": display} if display else {}),
            }
        ]
    }


def care_plan_body(patient_id: int | None = None, **extra) -> dict:
    """A valid minimal CarePlan: R4 requires `status`, `intent` and `subject`. With no patient the
    subject is an absolute URL (not existence-checked)."""
    subject = {
        "reference": f"Patient/{patient_id}"
        if patient_id
        else "https://other.example.org/fhir/Patient/1"
    }
    return {"status": "active", "intent": "plan", "subject": subject, **extra}


def full_body(
    organization_id: int,
    patient_id: int,
    practitioner_id: int,
    encounter_id: int,
    condition_id: int,
    care_team_id: int,
    service_request_id: int,
    location_id: int,
    medication_id: int,
    other_care_plan_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return care_plan_body(
        patient_id,
        resourceType="CarePlan",
        identifier=[
            {
                "system": CARE_PLAN_IDS,
                "value": "CP-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        instantiatesCanonical=["http://example.org/fhir/PlanDefinition/diabetes|1.0"],
        instantiatesUri=["http://example.org/protocols/diabetes"],
        basedOn=[{"reference": f"CarePlan/{other_care_plan_id}"}],
        replaces=[{"reference": f"CarePlan/{other_care_plan_id}"}],
        partOf=[{"reference": f"CarePlan/{other_care_plan_id}"}],
        category=[concept(CATEGORY, "assess-plan", "Assessment and plan")],
        title="Diabetes management plan",
        description="Long-term management of type 2 diabetes.",
        encounter={"reference": f"Encounter/{encounter_id}"},
        period={"start": "2026-01-01", "end": "2026-06-30"},
        created="2026-01-01T09:00:00Z",
        author={"reference": f"Practitioner/{practitioner_id}"},
        contributor=[{"reference": f"Practitioner/{practitioner_id}"}],
        careTeam=[{"reference": f"CareTeam/{care_team_id}"}],
        addresses=[{"reference": f"Condition/{condition_id}"}],
        supportingInfo=[{"reference": f"Condition/{condition_id}"}],
        goal=[{"reference": "https://other.example.org/fhir/Goal/1"}],
        activity=[
            {
                "outcomeCodeableConcept": [concept(SCT, "385669000", "Successful")],
                "outcomeReference": [{"reference": f"Condition/{condition_id}"}],
                "progress": [{"text": "On track", "time": "2026-03-01T10:00:00Z"}],
                "reference": {"reference": f"ServiceRequest/{service_request_id}"},
            },
            {
                "detail": {
                    "kind": "ServiceRequest",
                    "instantiatesCanonical": [
                        "http://example.org/fhir/ActivityDefinition/exercise"
                    ],
                    "instantiatesUri": ["http://example.org/protocols/exercise"],
                    "code": concept(SCT, "386053000", "Evaluation procedure"),
                    "reasonCode": [concept(SCT, "73211009", "Diabetes mellitus")],
                    "reasonReference": [{"reference": f"Condition/{condition_id}"}],
                    "goal": [{"reference": "https://other.example.org/fhir/Goal/1"}],
                    "status": "in-progress",
                    "statusReason": {"text": "Started"},
                    "doNotPerform": False,
                    "scheduledPeriod": {"start": "2026-02-01", "end": "2026-02-28"},
                    "location": {"reference": f"Location/{location_id}"},
                    "performer": [{"reference": f"Practitioner/{practitioner_id}"}],
                    "productReference": {"reference": f"Medication/{medication_id}"},
                    "dailyAmount": {"value": 2, "unit": "mg"},
                    "quantity": {"value": 10, "unit": "mg"},
                    "description": "Daily walk.",
                }
            },
        ],
        note=[
            {
                "authorReference": {"reference": f"Practitioner/{practitioner_id}"},
                "time": "2026-02-01T10:00:00Z",
                "text": "Review monthly.",
            }
        ],
    )


async def create_care_plan(client, body: dict) -> int:
    """Create a care plan and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
