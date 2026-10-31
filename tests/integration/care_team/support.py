"""Shared helpers and payloads for care_team integration tests."""

BASE = "/api/fhir/v1/care-teams"
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


async def create_test_organization(client) -> int:
    """Create a minimal organization and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/organizations/",
        json={"name": "Acme Health System", "active": True},
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


def minimal_care_team(patient_id: int) -> dict:
    return {
        "status": "active",
        "name": "Minimal Care Team",
        "subject": f"Patient/{patient_id}",
    }


def full_care_team(
    patient_id: int,
    practitioner_id: int | None = None,
    org_id: int | None = None,
    condition_id: int | None = None,
) -> dict:
    payload = {
        "status": "active",
        "name": "Comprehensive Cardiology Care Team",
        "subject": f"Patient/{patient_id}",
        "subject_display": "Jane Doe",
        "period_start": "2026-01-01T00:00:00Z",
        "period_end": "2026-12-31T23:59:59Z",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "LA27976-2",
                        "display": "Longitudinal care-coordination",
                    }
                ],
                "text": "Longitudinal care-coordination",
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": "+1-555-555-5555",
                "use": "work",
            }
        ],
        "note": [
            {
                "text": "Initial care team established following diagnosis.",
            }
        ],
    }
    if practitioner_id:
        participant_data = {
            "member": f"Practitioner/{practitioner_id}",
            "member_display": "Dr. Adam Careful",
            "role": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "407542009",
                            "display": "Cardiologist",
                        }
                    ],
                    "text": "Lead Cardiologist",
                }
            ],
        }
        if org_id:
            participant_data["on_behalf_of"] = f"Organization/{org_id}"
            participant_data["on_behalf_of_display"] = "Acme Health System"
        payload["participant"] = [participant_data]
    if org_id:
        payload["managing_organization"] = [f"Organization/{org_id}"]
    if condition_id:
        payload["reason_reference"] = [f"Condition/{condition_id}"]
    return payload


async def create_care_team(client, **overrides) -> dict:
    """Helper to create a CareTeam and return the response JSON."""
    p_id = overrides.pop("patient_id", None)
    if not p_id:
        p_id = await create_test_patient(client)
    body = minimal_care_team(p_id)
    body.update(overrides)
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()
