"""Shared helpers and payloads for care_plan integration tests."""

BASE = "/api/fhir/v1/care-plans"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_patient(client) -> int:
    """Create a minimal patient and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/patients/",
        json={"active": True, "name": [{"family": "Doe", "given": ["Jane"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_practitioner(client) -> int:
    """Create a minimal practitioner and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/practitioners/",
        json={"active": True, "name": [{"family": "Careful", "given": ["Adam"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_condition(client, patient_id: int) -> int:
    """Create a minimal condition and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/conditions/",
        json={
            "clinical_status": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                    }
                ]
            },
            "verification_status": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed",
                    }
                ]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_care_plan(patient_id: int) -> dict:
    return {
        "status": "active",
        "intent": "plan",
        "subject": f"Patient/{patient_id}",
    }


def full_care_plan(
    patient_id: int,
    practitioner_id: int | None = None,
    condition_id: int | None = None,
) -> dict:
    payload = {
        "status": "active",
        "intent": "plan",
        "title": "Diabetes Care Plan",
        "description": "Comprehensive diabetes management plan",
        "subject": f"Patient/{patient_id}",
        "subject_display": "Jane Doe",
        "period_start": "2026-01-01T00:00:00Z",
        "period_end": "2026-12-31T23:59:59Z",
        "created": "2026-01-01T12:00:00Z",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "698360004",
                        "display": "Diabetes self management plan",
                    }
                ],
                "text": "Diabetes self management plan",
            }
        ],
        "activity": [
            {
                "detail": {
                    "kind": "CommunicationRequest",
                    "status": "in-progress",
                    "description": "Patient education on insulin self-administration",
                    "do_not_perform": False,
                }
            }
        ],
        "note": [
            {
                "text": "Initial plan established following diagnosis.",
            }
        ],
    }
    if practitioner_id:
        payload["author"] = f"Practitioner/{practitioner_id}"
        payload["author_display"] = "Dr. Adam Careful"
    if condition_id:
        payload["addresses"] = [f"Condition/{condition_id}"]
    return payload


async def create_care_plan(client, **overrides) -> dict:
    """Helper to create a CarePlan and return the response JSON."""
    p_id = overrides.pop("patient_id", None)
    if not p_id:
        p_id = await create_test_patient(client)
    body = minimal_care_plan(p_id)
    body.update(overrides)
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()
