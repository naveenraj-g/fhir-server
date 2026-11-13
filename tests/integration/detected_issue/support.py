"""Shared helpers and payloads for DetectedIssue integration tests."""

BASE = "/api/fhir/v1/detected-issues"
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
        json={"active": True, "name": [{"family": "Smith", "given": ["Alice"]}]},
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


async def create_test_observation(client, patient_id: int) -> int:
    """Create a minimal observation and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/observations/",
        json={
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8867-4",
                        "display": "Heart rate",
                    }
                ]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
        },
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
    return int(resp.json()["id"])


def minimal_detected_issue(patient_id: int | None = None) -> dict:
    payload = {
        "status": "final",
    }
    if patient_id:
        payload["patient"] = {"reference": f"Patient/{patient_id}"}
    return payload


async def create_detected_issue(client, patient_id: int | None = None) -> int:
    """Create a minimal detected issue and return its public ID."""
    resp = await client.post(
        f"{BASE}/",
        json=minimal_detected_issue(patient_id),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def full_detected_issue(
    patient_id: int,
    practitioner_id: int | None = None,
    condition_id: int | None = None,
    observation_id: int | None = None,
    organization_id: int | None = None,
) -> dict:
    payload = {
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "DRG",
                    "display": "Drug Interaction Alert",
                }
            ],
            "text": "Potential drug-drug interaction between Warfarin and Aspirin",
        },
        "severity": "high",
        "patient": {
            "reference": f"Patient/{patient_id}",
            "reference_display": "Jane Doe",
        },
        "identified_date_time": "2026-02-01T10:00:00Z",
        "detail": "Concurrent use of warfarin and aspirin significantly increases risk of major gastrointestinal hemorrhage.",
        "reference": "http://example.org/alerts/interaction-war-asp",
        "evidence": [
            {
                "code": [
                    {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "89240000",
                                "display": "Drug-induced hemorrhage",
                            }
                        ],
                        "text": "Bleeding complication risk",
                    }
                ],
            }
        ],
        "mitigation": [
            {
                "action": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                            "code": "13",
                            "display": "Consulted Prescriber",
                        }
                    ],
                    "text": "Prescriber confirmed low-dose aspirin is indicated.",
                },
                "date": "2026-02-01T10:30:00Z",
            }
        ],
        "identifier": [
            {
                "use": "official",
                "system": "http://example.org/issues",
                "value": "ISSUE-2026-001",
            }
        ],
    }

    if practitioner_id:
        payload["author"] = {
            "reference": f"Practitioner/{practitioner_id}",
            "reference_display": "Dr. Alice Smith",
        }
        payload["mitigation"][0]["author"] = {
            "reference": f"Practitioner/{practitioner_id}",
            "reference_display": "Dr. Alice Smith",
        }

    if condition_id:
        payload["implicated"] = [
            {
                "reference": f"Condition/{condition_id}",
                "reference_display": "Atrial Fibrillation",
            }
        ]

    if observation_id:
        payload["evidence"][0]["detail"] = [
            {
                "reference": f"Observation/{observation_id}",
                "reference_display": "INR Lab Result",
            }
        ]

    if organization_id:
        payload["identifier"][0]["assigner"] = f"Organization/{organization_id}"
        payload["identifier"][0]["assigner_display"] = "Acme Clinic"

    return payload
