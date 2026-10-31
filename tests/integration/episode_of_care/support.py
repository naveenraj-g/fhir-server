"""Shared helpers and payloads for episode_of_care integration tests."""

BASE = "/api/fhir/v1/episodes-of-care"
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
        json={"active": True, "name": [{"family": "House", "given": ["Gregory"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_organization(client) -> int:
    """Create a minimal organization and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/organizations/",
        json={"name": "Princeton-Plainsboro Teaching Hospital", "active": True},
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


async def create_test_care_team(client, patient_id: int) -> int:
    """Create a minimal care team and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/care-teams/",
        json={
            "status": "active",
            "name": "General Care Team",
            "subject": f"Patient/{patient_id}",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_episode_of_care(patient_id: int) -> dict:
    return {
        "status": "active",
        "patient": f"Patient/{patient_id}",
    }


def full_episode_of_care(
    patient_id: int,
    practitioner_id: int | None = None,
    org_id: int | None = None,
    condition_id: int | None = None,
    care_team_id: int | None = None,
) -> dict:
    payload = {
        "status": "active",
        "patient": f"Patient/{patient_id}",
        "patient_display": "Jane Doe",
        "period_start": "2026-01-01T00:00:00Z",
        "period_end": "2026-12-31T23:59:59Z",
        "status_history": [
            {
                "status": "planned",
                "period_start": "2025-12-01T00:00:00Z",
                "period_end": "2025-12-31T23:59:59Z",
            }
        ],
        "type": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/episodeofcare-type",
                        "code": "hacc",
                        "display": "Home and Community Care",
                    }
                ],
                "text": "Home and Community Care",
            }
        ],
        "identifier": [
            {
                "use": "official",
                "system": "http://example.org/episodes",
                "value": "EOC-12345",
            }
        ],
    }
    if org_id:
        payload["managing_organization"] = f"Organization/{org_id}"
        payload["managing_organization_display"] = "Princeton-Plainsboro Teaching Hospital"
    if practitioner_id:
        payload["care_manager"] = f"Practitioner/{practitioner_id}"
        payload["care_manager_display"] = "Dr. Gregory House"
    if condition_id:
        payload["diagnosis"] = [
            {
                "condition": f"Condition/{condition_id}",
                "condition_display": "Chronic Condition",
                "role": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
                            "code": "CC",
                            "display": "Chief complaint",
                        }
                    ],
                    "text": "Chief complaint",
                },
                "rank": 1,
            }
        ]
    if care_team_id:
        payload["team"] = [f"CareTeam/{care_team_id}"]
    return payload


async def create_episode_of_care(client, patient_id: int | None = None, **overrides) -> dict:
    if patient_id is None:
        patient_id = await create_test_patient(client)
    payload = minimal_episode_of_care(patient_id)
    payload.update(overrides)
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
