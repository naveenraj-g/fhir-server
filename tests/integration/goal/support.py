"""Shared helpers and payloads for goal integration tests."""

BASE = "/api/fhir/v1/goals"
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


async def create_test_organization(client) -> int:
    """Create a minimal organization and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/organizations/",
        json={"name": "Good Health Clinic"},
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


def minimal_goal(patient_id: int) -> dict:
    return {
        "lifecycle_status": "active",
        "description_text": "Follow-up dietary regime",
        "subject": f"Patient/{patient_id}",
    }


def full_goal(
    patient_id: int,
    practitioner_id: int,
    organization_id: int,
    condition_id: int,
) -> dict:
    return {
        "lifecycle_status": "active",
        "achievement_status_coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/goal-achievement",
                "code": "in-progress",
                "display": "In Progress",
            }
        ],
        "achievement_status_text": "In Progress",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/goal-category",
                        "code": "dietary",
                        "display": "Dietary",
                    }
                ],
                "text": "Dietary",
            }
        ],
        "priority_coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/goal-priority",
                "code": "high-priority",
                "display": "High Priority",
            }
        ],
        "priority_text": "High Priority",
        "description_coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "281036007",
                "display": "Follow-up dietary regime",
            }
        ],
        "description_text": "Follow-up dietary regime",
        "subject": f"Patient/{patient_id}",
        "subject_display": "Jane Doe",
        "start_date": "2026-01-01",
        "target": [
            {
                "measure_text": "Weight",
                "detail_quantity_value": 70,
                "detail_quantity_unit": "kg",
                "detail_quantity_system": "http://unitsofmeasure.org",
                "detail_quantity_code": "kg",
                "due_date": "2026-06-01",
            }
        ],
        "status_date": "2026-01-01",
        "status_reason": "Patient willing to adhere to diet",
        "expressed_by": f"Practitioner/{practitioner_id}",
        "expressed_by_display": "Dr. Smith",
        "addresses": [f"Condition/{condition_id}"],
        "note": ["Patient motivated to follow diet plan."],
        "outcome_code": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "429074003",
                        "display": "Normal weight",
                    }
                ],
                "text": "Normal weight achieved",
            }
        ],
        "identifier": [
            {
                "use": "official",
                "system": "http://hospital.example.org",
                "value": "GOAL-123",
                "assigner": f"Organization/{organization_id}",
                "assigner_display": "Good Health Clinic",
            }
        ],
    }
