"""Shared helpers and payloads for patient integration tests.

Request bodies are genuine FHIR R4 Patient JSON (camelCase, nested datatypes),
and every response is FHIR R4 too."""

from tests.integration.practitioner_role.support import (
    create_organization,
    create_practitioner,
)
from tests.integration.practitioner_role.support import (
    create_role as create_practitioner_role,
)

BASE = "/api/fhir/v1/patients"
API = "/api/fhir/v1"

MRN = "http://hospital.example.org/mrn"
LANG = "urn:ietf:bcp:47"

MINIMAL = {
    "active": True,
    "name": [{"family": "Chalmers", "given": ["Peter"]}],
}

# No `system` on the coded fields below deliberately — an external-terminology
# system can trigger a slow remote lookup in the java validator sidecar.
FULL = {
    "resourceType": "Patient",
    "active": True,
    "gender": "male",
    "birthDate": "1974-12-25",
    "deceasedBoolean": False,
    "multipleBirthBoolean": False,
    "maritalStatus": {
        "coding": [{"code": "M", "display": "Married"}],
        "text": "Married",
    },
    "identifier": [
        {
            "use": "official",
            "system": MRN,
            "value": "MRN-12345",
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "MR",
                    }
                ]
            },
        }
    ],
    "name": [
        {
            "use": "official",
            "family": "Chalmers",
            "given": ["Peter", "James"],
            "prefix": ["Mr"],
        }
    ],
    "telecom": [
        {"system": "phone", "value": "555-1234", "use": "home"},
        {"system": "email", "value": "peter@example.org"},
    ],
    "address": [
        {
            "use": "home",
            "line": ["534 Erewhon St"],
            "city": "PleasantVille",
            "state": "Vic",
            "postalCode": "3999",
            "country": "AU",
        }
    ],
    # No `contentType` deliberately — Attachment.contentType is bound against the
    # full IANA MimeType ValueSet and the sidecar tries a remote lookup for it.
    "photo": [{"url": "https://fhir-server.dev/fhir/assets/patient.png"}],
    "contact": [
        {
            "relationship": [{"coding": [{"code": "N", "display": "Next-of-Kin"}]}],
            "name": {"family": "Chalmers", "given": ["Sarah"]},
            "gender": "female",
            "telecom": [{"system": "phone", "value": "555-9876", "use": "mobile"}],
        }
    ],
    "communication": [
        {
            "language": {"coding": [{"code": "en", "display": "English"}]},
            "preferred": True,
        }
    ],
}


async def link_user(client, patient_id: int, user_id: str = "u-test"):
    """Link an end-user to a patient (needs patient:link)."""
    return await client.put(f"{BASE}/{patient_id}/user", json={"user_id": user_id})


async def create_patient(client, payload=None) -> int:
    """Create a patient and return the public patient id (int)."""
    resp = await client.post(BASE + "/", json=payload or MINIMAL)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
