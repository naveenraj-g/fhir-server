"""Shared helpers and payloads for MedicationStatement integration tests."""

BASE = "/api/fhir/v1/medication-statements"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_patient(client) -> int:
    """Create a minimal patient and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/patients/",
        json={"active": True, "name": [{"family": "Doe", "given": ["Jane"]}]},
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


def minimal_medication_statement(patient_id: int) -> dict:
    return {
        "status": "active",
        "subject": {
            "reference": f"Patient/{patient_id}",
            "reference_display": "Jane Doe",
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
    }


def full_medication_statement(
    patient_id: int, condition_id: int | None = None
) -> dict:
    payload = {
        "status": "active",
        "subject": {
            "reference": f"Patient/{patient_id}",
            "reference_display": "Jane Doe",
        },
        "category": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
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
        "effective_date_time": "2026-01-15T10:00:00Z",
        "date_asserted": "2026-01-15T10:00:00Z",
        "information_source": {
            "reference": f"Patient/{patient_id}",
            "reference_display": "Jane Doe",
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
                "text": "Patient reports taking medication regularly with meals.",
                "time": "2026-01-15T10:05:00Z",
                "author_string": "Dr. Alice Smith",
            }
        ],
        "dosage": [
            {
                "sequence": 1,
                "text": "Take 1 capsule by mouth three times daily with food.",
                "timing": {"code": {"text": "TID"}},
                "as_needed_boolean": False,
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
            }
        ],
    }
    if condition_id:
        payload["reason_reference"] = [{"reference": f"Condition/{condition_id}"}]
    return payload


async def create_medication_statement(
    client, payload: dict, headers: dict | None = None
) -> dict:
    resp = await client.post(BASE + "/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()
