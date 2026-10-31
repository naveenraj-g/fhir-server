"""Shared helpers and payloads for related_person integration tests."""

BASE = "/api/fhir/v1/related_persons"
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
        json={"name": "Good Health Clinic"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_related_person(patient_id: int) -> dict:
    return {
        "patient": f"Patient/{patient_id}",
        "patient_display": "Jane Doe",
    }


def full_related_person(patient_id: int, org_id: int | None = None) -> dict:
    payload = {
        "active": True,
        "patient": f"Patient/{patient_id}",
        "patient_display": "Jane Doe",
        "relationship": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                        "code": "MTH",
                        "display": "Mother",
                    }
                ],
                "text": "Mother",
            }
        ],
        "name": [
            {
                "use": "official",
                "family": "Smith",
                "given": ["Alice"],
                "prefix": ["Dr."],
                "suffix": ["MD"],
                "text": "Dr. Alice Smith",
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": "555-0100",
                "use": "home",
                "rank": 1,
            }
        ],
        "gender": "female",
        "birth_date": "1980-05-21",
        "address": [
            {
                "use": "home",
                "type": "postal",
                "line": ["534 Erewhon St"],
                "city": "Pleasantville",
                "state": "Vic",
                "postal_code": "3999",
                "country": "AU",
            }
        ],
        "photo": [
            {
                "content_type": "image/jpeg",
                "url": "http://example.org/photo.jpg",
                "title": "Photo",
            }
        ],
        "period_start": "2020-01-01T00:00:00Z",
        "period_end": "2030-01-01T00:00:00Z",
        "communication": [
            {
                "language_coding": [
                    {
                        "system": "urn:ietf:bcp:47",
                        "code": "en",
                        "display": "English",
                    }
                ],
                "language_text": "English",
                "preferred": True,
            }
        ],
        "identifier": [
            {
                "use": "official",
                "type_coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "MR",
                        "display": "Medical Record Number",
                    }
                ],
                "type_text": "Medical Record Number",
                "system": "urn:oid:1.2.3.4",
                "value": "RP12345",
                "period_start": "2020-01-01T00:00:00Z",
                "period_end": "2030-01-01T00:00:00Z",
            }
        ],
    }
    if org_id is not None:
        payload["identifier"][0]["assigner"] = f"Organization/{org_id}"
        payload["identifier"][0]["assigner_display"] = "Good Health Clinic"
    return payload
