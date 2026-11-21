"""Shared helpers and payloads for related-person integration tests.

Request bodies are genuine FHIR R4 RelatedPerson JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

# The resources a RelatedPerson points at (and that point at it) are created through their own routers.
from tests.integration.appointment.support import (  # noqa: F401
    appointment_body,
    create_appointment,
    create_organization,
    create_patient,
    create_practitioner,
    participant,
)

BASE = "/api/fhir/v1/related-persons"
API = "/api/fhir/v1"

RP_IDS = "https://fhir-server.dev/fhir/identifier-system/related-person-id"
ROLE = "http://terminology.hl7.org/CodeSystem/v3-RoleCode"


def related_person_body(patient_id: int | None = None, **extra) -> dict:
    """A valid minimal RelatedPerson: R4 requires `patient`. With no patient the
    reference is an absolute URL (not existence-checked)."""
    patient = {
        "reference": f"Patient/{patient_id}"
        if patient_id
        else "https://other.example.org/fhir/Patient/1"
    }
    return {"patient": patient, **extra}


def full_body(patient_id: int, organization_id: int) -> dict:
    return related_person_body(
        patient_id,
        resourceType="RelatedPerson",
        identifier=[
            {
                "system": RP_IDS,
                "value": "RP-1001",
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
        active=True,
        relationship=[
            {
                "coding": [{"system": ROLE, "code": "MTH", "display": "mother"}],
                "text": "Mother",
            }
        ],
        name=[
            {
                "use": "official",
                "family": "Windsor",
                "given": ["Mary", "Ann"],
                "prefix": ["Mrs"],
            }
        ],
        telecom=[
            {"system": "phone", "value": "555-9988", "use": "mobile"},
            {"system": "email", "value": "mary@example.org"},
        ],
        gender="female",
        birthDate="1965-04-12",
        address=[
            {
                "use": "home",
                "line": ["1 Main St"],
                "city": "Boston",
                "state": "MA",
                "postalCode": "02110",
                "country": "US",
            }
        ],
        photo=[{"contentType": "image/png", "url": "https://example.org/mary.png"}],
        period={"start": "2020-01-01"},
        communication=[{"language": {"coding": [{"code": "en"}]}, "preferred": True}],
    )


async def create_related_person(client, body: dict) -> int:
    """Create a related person and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
