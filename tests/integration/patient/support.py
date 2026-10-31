"""Shared helpers and payloads for patient integration tests."""

BASE = "/api/fhir/v1/patients"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}

MINIMAL = {
    "active": True,
    "name": [{"family": "Chalmers", "given": ["Peter"]}],
}

FULL = {
    "user_id": "end-user-1",
    "active": True,
    "gender": "male",
    "birth_date": "1974-12-25",
    "deceased_boolean": False,
    "marital_status_text": "Married",
    "marital_status_coding": [
        {"code": "M", "display": "Married"}
    ],
    "multiple_birth_boolean": False,
    "identifier": [
        {
            "use": "official",
            "system": "http://hospital.example.com/mrn",
            "value": "MRN-12345",
            "type_coding": [{"code": "MR"}],
        }
    ],
    "name": [
        {
            "use": "official",
            "family": "Chalmers",
            "given": ["Peter", "James"],
            "prefix": ["Mr."],
        }
    ],
    "telecom": [
        {"system": "phone", "value": "+1-555-123-4567", "use": "home"}
    ],
    "address": [
        {
            "use": "home",
            "type": "physical",
            "line": ["534 Erewhon St"],
            "city": "PleasantVille",
            "state": "Vic",
            "postal_code": "3999",
            "country": "AU",
        }
    ],
    "photo": [
        {"url": "https://fhir-server.dev/fhir/assets/patient.png"}
    ],
    "contact": [
        {
            "relationship": [
                {"coding": [{"code": "N", "display": "Next-of-Kin"}]}
            ],
            "name_family": "Chalmers",
            "name_given": ["Sarah"],
            "gender": "female",
            "telecom": [
                {"system": "phone", "value": "+1-555-987-6543", "use": "mobile"}
            ],
        }
    ],
    "communication": [
        {"language_coding": [{"code": "en", "display": "English"}], "preferred": True}
    ],
}


async def create_patient(client, payload=None) -> int:
    """Create a patient and return the public patient id."""
    payload = payload or MINIMAL
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
