"""Shared helpers and payloads for condition integration tests.

Request bodies are genuine FHIR R4 Condition JSON (camelCase, nested datatypes),
and every response is FHIR R4 too."""

# The resources a Condition points at (and that point back at it) are created
# through their own routers.
from tests.integration.appointment.support import (  # noqa: F401
    appointment_body,
    create_appointment,
    participant,
)
from tests.integration.encounter.support import create_encounter, encounter_body  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)
from tests.integration.related_person.support import create_related_person, related_person_body  # noqa: F401

BASE = "/api/fhir/v1/conditions"
API = "/api/fhir/v1"

COND_IDS = "https://fhir-server.dev/fhir/identifier-system/condition-id"
CLIN = "http://terminology.hl7.org/CodeSystem/condition-clinical"
VERIF = "http://terminology.hl7.org/CodeSystem/condition-ver-status"
CATEGORY = "http://terminology.hl7.org/CodeSystem/condition-category"
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"


def clinical(code: str = "active") -> dict:
    return {"coding": [{"system": CLIN, "code": code}]}


def verification(code: str = "confirmed") -> dict:
    return {"coding": [{"system": VERIF, "code": code}]}


def category(code: str = "problem-list-item") -> dict:
    return {"coding": [{"system": CATEGORY, "code": code}]}


def condition_body(patient_id: int | None = None, **extra) -> dict:
    """A valid minimal Condition: R4 requires `subject`. With no patient the
    reference is an absolute URL (not existence-checked)."""
    subject = {"reference": f"Patient/{patient_id}" if patient_id else "https://other.example.org/fhir/Patient/1"}
    return {"subject": subject, **extra}


def full_body(patient_id: int, encounter_id: int, practitioner_id: int, organization_id: int) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return condition_body(
        patient_id,
        resourceType="Condition",
        identifier=[
            {
                "system": COND_IDS,
                "value": "C-1001",
                "type": {"coding": [{"system": V2_0203, "code": "PRN"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        clinicalStatus=clinical("active"),
        verificationStatus=verification("confirmed"),
        category=[category("problem-list-item")],
        severity={"coding": [{"system": SCT, "code": "24484000", "display": "Severe"}]},
        code={"coding": [{"system": SCT, "code": "38341003", "display": "Hypertension"}], "text": "High blood pressure"},
        bodySite=[{"coding": [{"system": SCT, "code": "368208006", "display": "Left upper arm"}]}],
        encounter={"reference": f"Encounter/{encounter_id}"},
        onsetDateTime="2023-01-15T09:30:00Z",
        recordedDate="2023-01-15T10:00:00Z",
        recorder={"reference": f"Practitioner/{practitioner_id}"},
        asserter={"reference": f"Patient/{patient_id}"},
        stage=[
            {
                "summary": {"coding": [{"system": SCT, "code": "14803004", "display": "Temporary"}]},
                "assessment": [{"reference": "Observation/160001"}],
                "type": {"text": "clinical"},
            }
        ],
        evidence=[
            {
                "code": [{"coding": [{"system": SCT, "code": "29857009", "display": "Chest pain"}]}],
                "detail": [{"reference": "Observation/160001"}],
            }
        ],
        note=[
            {
                "authorReference": {"reference": f"Practitioner/{practitioner_id}"},
                "time": "2023-01-15T10:05:00Z",
                "text": "Blood pressure poorly controlled.",
            }
        ],
    )


async def create_condition(client, body: dict) -> int:
    """Create a condition and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
