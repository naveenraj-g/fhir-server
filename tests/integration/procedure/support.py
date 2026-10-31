"""Shared helpers and payloads for procedure integration tests."""

BASE = "/api/fhir/v1/procedures"
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
        json={"active": True, "name": [{"family": "Surgeon", "given": ["Jack"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_location(client) -> int:
    """Create a minimal location and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/locations/",
        json={"name": "Operating Room 1", "status": "active"},
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


def minimal_procedure(patient_id: int) -> dict:
    return {
        "status": "completed",
        "subject": f"Patient/{patient_id}",
    }


def full_procedure(
    patient_id: int,
    practitioner_id: int | None = None,
    condition_id: int | None = None,
    location_id: int | None = None,
) -> dict:
    payload = {
        "status": "completed",
        "subject": f"Patient/{patient_id}",
        "subject_display": "Jane Doe",
        "performed_date_time": "2026-01-01T10:00:00Z",
        "category": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "387713003",
                    "display": "Surgical procedure",
                }
            ],
            "text": "Surgical procedure",
        },
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "80146002",
                    "display": "Appendectomy",
                }
            ],
            "text": "Appendectomy",
        },
        "outcome": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "385669000",
                    "display": "Successful",
                }
            ],
            "text": "Successful",
        },
        "reason_code": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "85189001",
                        "display": "Acute appendicitis",
                    }
                ],
                "text": "Acute appendicitis",
            }
        ],
        "body_site": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "66754008",
                        "display": "Appendix structure",
                    }
                ],
                "text": "Appendix structure",
            }
        ],
        "note": [
            {
                "text": "Procedure carried out under general anesthesia without complications.",
                "author_string": "Dr. Jack Surgeon",
            }
        ],
    }

    if practitioner_id:
        payload["performer"] = [
            {
                "actor": f"Practitioner/{practitioner_id}",
                "actor_display": "Dr. Jack Surgeon",
                "function": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "304292004",
                            "display": "Surgeon",
                        }
                    ],
                    "text": "Primary Surgeon",
                },
            }
        ]
        payload["recorder"] = f"Practitioner/{practitioner_id}"
        payload["recorder_display"] = "Dr. Jack Surgeon"

    if condition_id:
        payload["reason_reference"] = [f"Condition/{condition_id}"]

    if location_id:
        payload["location"] = f"Location/{location_id}"
        payload["location_display"] = "Operating Room 1"

    return payload


async def create_procedure(client, payload: dict, headers: dict | None = None) -> dict:
    resp = await client.post(BASE + "/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()
