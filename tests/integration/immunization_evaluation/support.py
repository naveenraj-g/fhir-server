"""Shared helpers and payloads for ImmunizationEvaluation integration tests."""

BASE = "/api/fhir/v1/immunization-evaluations"
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
        json={"active": True, "name": "Acme Clinic"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_immunization(client, patient_id: int) -> int:
    """Create a minimal immunization and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/immunizations/",
        json={
            "status": "completed",
            "vaccine_code": {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/sid/cvx",
                        "code": "197",
                        "display": "influenza",
                    }
                ],
                "text": "Flu vaccine",
            },
            "patient": {"reference": f"Patient/{patient_id}"},
            "occurrence_date_time": "2026-02-01T10:00:00Z",
            "primary_source": True,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_immunization_evaluation(patient_id: int, immunization_id: int) -> dict:
    return {
        "status": "completed",
        "patient": {"reference": f"Patient/{patient_id}"},
        "target_disease": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "14189004",
                    "display": "Measles",
                }
            ],
            "text": "Measles",
        },
        "immunization_event": {"reference": f"Immunization/{immunization_id}"},
        "dose_status": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status",
                    "code": "valid",
                    "display": "Valid",
                }
            ],
            "text": "Valid",
        },
    }


def full_immunization_evaluation(
    patient_id: int, immunization_id: int, org_id: int | None = None
) -> dict:
    payload = minimal_immunization_evaluation(patient_id, immunization_id)
    payload.update(
        {
            "date": "2026-02-01T10:00:00Z",
            "description": "Routine evaluation of MMR dose 1",
            "series": "MMR standard series",
            "dose_number_positive_int": 1,
            "series_doses_positive_int": 2,
            "dose_status_reason": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status-reason",
                            "code": "valid",
                            "display": "Valid administration",
                        }
                    ],
                    "text": "Valid administration per guidelines",
                }
            ],
            "identifier": [
                {
                    "use": "official",
                    "system": "http://example.org/eval-ids",
                    "value": "EVAL-12345",
                }
            ],
        }
    )
    if org_id:
        payload["authority"] = {"reference": f"Organization/{org_id}"}
    return payload


async def create_immunization_evaluation(
    client, patient_id: int, immunization_id: int
) -> int:
    resp = await client.post(
        f"{BASE}/",
        json=minimal_immunization_evaluation(patient_id, immunization_id),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
