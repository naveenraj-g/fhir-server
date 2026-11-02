"""Shared helpers and payloads for FamilyMemberHistory integration tests."""

BASE = "/api/fhir/v1/family-member-histories"
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


def minimal_family_member_history(patient_id: int) -> dict:
    return {
        "status": "completed",
        "patient": f"Patient/{patient_id}",
        "relationship": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "FTH",
                    "display": "father",
                }
            ],
            "text": "Father",
        },
    }


def full_family_member_history(
    patient_id: int, condition_id: int | None = None
) -> dict:
    payload = {
        "status": "completed",
        "patient": f"Patient/{patient_id}",
        "patient_display": "Jane Doe",
        "date": "2026-01-15T10:00:00Z",
        "name": "John Doe",
        "relationship": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "FTH",
                    "display": "father",
                }
            ],
            "text": "Father",
        },
        "sex": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/administrative-gender",
                    "code": "male",
                    "display": "Male",
                }
            ],
            "text": "Male",
        },
        "born_date": "1950-05-12",
        "age_age_value": 75.0,
        "age_age_unit": "a",
        "age_age_system": "http://unitsofmeasure.org",
        "age_age_code": "a",
        "estimated_age": False,
        "deceased_boolean": False,
        "reason_code": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "44054006",
                        "display": "Type 2 diabetes mellitus",
                    }
                ],
                "text": "Family history of Type 2 Diabetes",
            }
        ],
        "note": [
            {
                "text": "Father was diagnosed with diabetes in his early 50s.",
                "time": "2026-01-15T10:05:00Z",
                "author_string": "Dr. Alice Smith",
            }
        ],
        "condition": [
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "44054006",
                            "display": "Type 2 diabetes mellitus",
                        }
                    ],
                    "text": "Type 2 Diabetes",
                },
                "outcome": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-outcome",
                            "code": "alive",
                            "display": "Alive",
                        }
                    ],
                    "text": "Alive and well managed",
                },
                "contributed_to_death": False,
                "onset_age_value": 52.0,
                "onset_age_unit": "a",
                "onset_age_system": "http://unitsofmeasure.org",
                "onset_age_code": "a",
                "note": [
                    {
                        "text": "Managed with oral metformin and lifestyle interventions.",
                        "time": "2026-01-15T10:06:00Z",
                    }
                ],
            }
        ],
    }
    if condition_id:
        payload["reason_reference"] = [{"reference": f"Condition/{condition_id}"}]
    return payload


async def create_family_member_history(
    client, payload: dict, headers: dict | None = None
) -> dict:
    resp = await client.post(BASE + "/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()
