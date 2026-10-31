"""Shared helpers and payloads for group integration tests."""

BASE = "/api/fhir/v1/groups"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_patient(client) -> int:
    """Create a minimal patient and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/patients/",
        json={"active": True, "name": [{"family": "Doe", "given": ["Jane"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_organization(client) -> int:
    """Create a minimal organization and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/organizations/",
        json={"active": True, "name": "General Hospital"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_group() -> dict:
    return {
        "type": "person",
        "actual": True,
    }


def full_group(patient_id: int, org_id: int | None = None) -> dict:
    payload = {
        "type": "person",
        "actual": True,
        "active": True,
        "name": "Diabetes Support Group",
        "quantity": 1,
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "394582007",
                    "display": "Community health",
                }
            ],
            "text": "Community health",
        },
        "identifier": [
            {
                "use": "official",
                "system": "http://example.org/groups",
                "value": "GRP-001",
            }
        ],
        "characteristic": [
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "73211009",
                            "display": "Diabetes mellitus",
                        }
                    ],
                    "text": "Diabetes mellitus",
                },
                "value_boolean": True,
                "exclude": False,
            }
        ],
        "member": [
            {
                "entity": f"Patient/{patient_id}",
                "entity_display": "Jane Doe",
                "inactive": False,
            }
        ],
    }
    if org_id:
        payload["managing_entity"] = f"Organization/{org_id}"
        payload["managing_entity_display"] = "General Hospital"
    return payload


async def create_group(client, payload: dict | None = None, patient_id: int | None = None) -> int:
    if payload is None:
        if patient_id is None:
            patient_id = await create_test_patient(client)
        payload = full_group(patient_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
