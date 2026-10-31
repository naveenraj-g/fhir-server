"""Shared helpers and payloads for condition integration tests."""

BASE = "/api/fhir/v1/conditions"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_patient(client) -> int:
    """Create a minimal patient and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/patients/",
        json={"active": True, "name": [{"family": "Doe", "given": ["Jane"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_condition(patient_id: int) -> dict:
    return {
        "subject": {
            "reference": f"Patient/{patient_id}",
            "reference_display": "Jane Doe",
        },
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "38341003",
                    "display": "Hypertension",
                }
            ],
            "text": "Hypertension",
        },
    }


def full_condition(patient_id: int) -> dict:
    return {
        "clinical_status": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                    "display": "Active",
                }
            ],
            "text": "Active",
        },
        "verification_status": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed",
                    "display": "Confirmed",
                }
            ],
            "text": "Confirmed",
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": "problem-list-item",
                        "display": "Problem List Item",
                    }
                ],
                "text": "Problem List Item",
            }
        ],
        "severity": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "24484000",
                    "display": "Severe",
                }
            ],
            "text": "Severe",
        },
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "38341003",
                    "display": "Hypertension",
                }
            ],
            "text": "Essential hypertension",
        },
        "body_site": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "368209003",
                        "display": "Right arm",
                    }
                ],
                "text": "Right arm",
            }
        ],
        "subject": {
            "reference": f"Patient/{patient_id}",
            "reference_display": "Jane Doe",
        },
        "onset_date_time": "2023-01-15T09:30:00Z",
        "abatement_string": "resolved after medication",
        "recorded_date": "2023-01-15T10:00:00Z",
        "identifier": [
            {
                "use": "official",
                "system": "http://hospital.example.com/conditions",
                "value": "COND-100456",
                "type_coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "MR",
                        "display": "Medical record number",
                    }
                ],
            }
        ],
        "stage": [
            {
                "summary": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "261614003",
                            "display": "Stage II",
                        }
                    ],
                    "text": "Stage II",
                },
                "type": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "260998006",
                            "display": "Clinical staging",
                        }
                    ],
                    "text": "Clinical staging",
                },
            }
        ],
        "evidence": [
            {
                "code": [
                    {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "25064002",
                                "display": "Headache",
                            }
                        ],
                        "text": "Headache",
                    }
                ]
            }
        ],
        "note": [
            {
                "author_string": "Dr. House",
                "time": "2023-01-15T10:05:00Z",
                "text": "Prescribed ACE inhibitors. Monitor blood pressure daily.",
            }
        ],
    }


async def create_condition(client, payload=None) -> int:
    """Create a condition and return the public condition id."""
    if payload is None:
        patient_id = await create_test_patient(client)
        payload = minimal_condition(patient_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
