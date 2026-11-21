"""Shared helpers and payloads for allergy_intolerance integration tests.

Request bodies are genuine FHIR R4 AllergyIntolerance JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

# The resources an AllergyIntolerance points at (and that it is searched through)
# are created through their own routers.
from tests.integration.encounter.support import create_encounter, encounter_body  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)
from tests.integration.related_person.support import (
    create_related_person,
    related_person_body,
)  # noqa: F401

BASE = "/api/fhir/v1/allergy-intolerances"
API = "/api/fhir/v1"

AI_IDS = "https://fhir-server.dev/fhir/identifier-system/allergy-id"
CLIN = "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
VERIF = "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification"
CATEGORY = "http://hl7.org/fhir/allergy-intolerance-category"
SEVERITY = "http://hl7.org/fhir/reaction-event-severity"
TYPE_SYSTEM = "http://hl7.org/fhir/allergy-intolerance-type"
CRITICALITY = "http://hl7.org/fhir/allergy-intolerance-criticality"
SCT = "http://snomed.info/sct"


def clinical(code: str = "active") -> dict:
    return {"coding": [{"system": CLIN, "code": code}]}


def verification(code: str = "confirmed") -> dict:
    return {"coding": [{"system": VERIF, "code": code}]}


def allergy_body(patient_id: int | None = None, **extra) -> dict:
    """A valid minimal AllergyIntolerance: R4 requires `patient`. With no patient
    the reference is an absolute URL (not existence-checked)."""
    patient = {
        "reference": f"Patient/{patient_id}"
        if patient_id
        else "https://other.example.org/fhir/Patient/1"
    }
    return {"patient": patient, **extra}


def full_body(
    patient_id: int, encounter_id: int, practitioner_id: int, organization_id: int
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return allergy_body(
        patient_id,
        resourceType="AllergyIntolerance",
        identifier=[
            {
                "system": AI_IDS,
                "value": "AI-1001",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "PRN",
                        }
                    ]
                },
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        clinicalStatus=clinical("active"),
        verificationStatus=verification("confirmed"),
        type="allergy",
        category=["food", "environment"],
        criticality="high",
        code={
            "coding": [{"system": SCT, "code": "227493005", "display": "Cashew nuts"}],
            "text": "Cashew nut allergy",
        },
        encounter={"reference": f"Encounter/{encounter_id}"},
        onsetDateTime="2023-01-15T09:30:00Z",
        recordedDate="2023-01-15T10:00:00Z",
        recorder={"reference": f"Practitioner/{practitioner_id}"},
        asserter={"reference": f"Patient/{patient_id}"},
        lastOccurrence="2023-06-01T12:00:00Z",
        note=[
            {
                "authorReference": {"reference": f"Practitioner/{practitioner_id}"},
                "time": "2023-01-15T10:05:00Z",
                "text": "Severe urticaria after cashew ingestion.",
            }
        ],
        reaction=[
            {
                "substance": {
                    "coding": [{"system": SCT, "code": "227493005"}],
                    "text": "Cashew",
                },
                "manifestation": [
                    {
                        "coding": [
                            {"system": SCT, "code": "64305001", "display": "Urticaria"}
                        ]
                    }
                ],
                "description": "Severe hives on face and neck",
                "onset": "2023-01-15T09:40:00Z",
                "severity": "severe",
                "exposureRoute": {
                    "coding": [
                        {"system": SCT, "code": "26643006", "display": "Oral route"}
                    ]
                },
                "note": [
                    {
                        "authorString": "Triage nurse",
                        "text": "Resolved after epinephrine.",
                    }
                ],
            }
        ],
    )


async def create_allergy_intolerance(client, body: dict) -> int:
    """Create an allergy / intolerance and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
