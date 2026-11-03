"""Shared helpers and payloads for MedicationAdministration integration tests."""

BASE = "/api/fhir/v1/medication-administrations"
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
        json={"active": True},
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


def minimal_medication_administration(patient_id: int) -> dict:
    return {
        "status": "completed",
        "subject": f"Patient/{patient_id}",
        "subject_display": "Jane Doe",
        "effective_date_time": "2026-01-15T10:00:00Z",
        "medication_codeable_concept": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "372687004",
                    "display": "Amoxicillin 500mg capsule",
                }
            ],
            "text": "Amoxicillin 500mg capsule",
        },
    }


def full_medication_administration(
    patient_id: int,
    practitioner_id: int | None = None,
    condition_id: int | None = None,
) -> dict:
    payload = {
        "status": "completed",
        "subject": f"Patient/{patient_id}",
        "subject_display": "Jane Doe",
        "effective_date_time": "2026-01-15T10:00:00Z",
        "category": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/med-admin-category",
                    "code": "inpatient",
                    "display": "Inpatient",
                }
            ],
            "text": "Inpatient",
        },
        "medication_codeable_concept": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "372687004",
                    "display": "Amoxicillin 500mg capsule",
                }
            ],
            "text": "Amoxicillin 500mg capsule",
        },
        "reason_code": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "87628006",
                        "display": "Bacterial infectious disease",
                    }
                ],
                "text": "Bacterial infection",
            }
        ],
        "note": [
            {
                "text": "Patient tolerated infusion without complications.",
                "time": "2026-01-15T10:30:00Z",
                "author_string": "Nurse Alice",
            }
        ],
        "dosage": {
            "text": "500mg oral capsule by mouth with water",
            "route": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "260548002",
                        "display": "Oral",
                    }
                ],
                "text": "Oral",
            },
            "dose": {
                "value": 500.0,
                "unit": "mg",
                "system": "http://unitsofmeasure.org",
                "code": "mg",
            },
        },
    }
    if practitioner_id:
        payload["performer"] = [
            {
                "actor": f"Practitioner/{practitioner_id}",
                "actor_display": "Dr. Bob Jones",
                "function": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/med-admin-perform-function",
                            "code": "performer",
                            "display": "Performer",
                        }
                    ],
                    "text": "Performer",
                },
            }
        ]
    if condition_id:
        payload["reason_reference"] = [{"reference": f"Condition/{condition_id}"}]
    return payload


async def create_medication_administration(
    client, payload: dict, headers: dict | None = None
) -> dict:
    resp = await client.post(BASE + "/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()
