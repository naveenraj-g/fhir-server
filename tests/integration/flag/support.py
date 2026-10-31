"""Shared helpers and payloads for flag integration tests."""

BASE = "/api/fhir/v1/flags"
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


async def create_test_practitioner(client) -> int:
    """Create a minimal practitioner and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/practitioners/",
        json={"active": True, "name": [{"family": "Smith", "given": ["Alice"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_encounter(client, patient_id: int) -> int:
    """Create a minimal encounter and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/encounters/",
        json={
            "status": "in-progress",
            "class_coding": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory",
            },
            "subject": f"Patient/{patient_id}",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_flag(patient_id: int) -> dict:
    return {
        "status": "active",
        "code_coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "399166001",
                "display": "Infection control precaution",
            }
        ],
        "code_text": "Infection control precaution",
        "subject": f"Patient/{patient_id}",
        "subject_display": "Jane Doe",
    }


def full_flag(
    patient_id: int,
    encounter_id: int | None = None,
    practitioner_id: int | None = None,
    org_id: int | None = None,
) -> dict:
    payload = {
        "status": "active",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/flag-category",
                        "code": "clinical",
                        "display": "Clinical",
                    }
                ],
                "text": "Clinical",
            }
        ],
        "code_coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "399166001",
                "display": "Infection control precaution",
            }
        ],
        "code_text": "Infection control precaution",
        "subject": f"Patient/{patient_id}",
        "subject_display": "Jane Doe",
        "period_start": "2026-01-01T00:00:00Z",
        "period_end": "2026-12-31T23:59:59Z",
        "identifier": [
            {
                "use": "official",
                "type_coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "FILL",
                        "display": "Filler Identifier",
                    }
                ],
                "type_text": "Filler Identifier",
                "system": "urn:oid:1.2.3.4",
                "value": "FLAG12345",
                "period_start": "2026-01-01T00:00:00Z",
                "period_end": "2026-12-31T23:59:59Z",
            }
        ],
    }
    if encounter_id is not None:
        payload["encounter"] = f"Encounter/{encounter_id}"
        payload["encounter_display"] = "Inpatient encounter"
    if practitioner_id is not None:
        payload["author"] = f"Practitioner/{practitioner_id}"
        payload["author_display"] = "Dr. Alice Smith"
    if org_id is not None:
        payload["identifier"][0]["assigner"] = f"Organization/{org_id}"
        payload["identifier"][0]["assigner_display"] = "Good Health Clinic"
    return payload
