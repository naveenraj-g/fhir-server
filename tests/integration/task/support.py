"""Shared helpers and payloads for task integration tests."""

BASE = "/api/fhir/v1/tasks"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_patient(client) -> int:
    """Create a minimal patient and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/patients/",
        json={"active": True, "name": [{"family": "Doe", "given": ["Jane"]}]},
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


async def create_test_practitioner(client) -> int:
    """Create a minimal practitioner and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/practitioners/",
        json={"active": True, "name": [{"family": "Smith", "given": ["Alice"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_location(client) -> int:
    """Create a minimal location and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/locations/",
        json={"name": "Examination Room 1", "status": "active"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_encounter(client, patient_id: int) -> int:
    """Create a minimal encounter and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/encounters/",
        json={
            "status": "in-progress",
            "class_coding": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory",
            },
            "subject": f"Patient/{patient_id}",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_task(patient_id: int) -> dict:
    return {
        "status": "requested",
        "intent": "order",
        "for": f"Patient/{patient_id}",
        "for_display": "Jane Doe",
    }


def full_task(
    patient_id: int,
    encounter_id: int | None = None,
    requester_id: int | None = None,
    owner_id: int | None = None,
    location_id: int | None = None,
    org_id: int | None = None,
) -> dict:
    payload = {
        "status": "requested",
        "intent": "order",
        "priority": "routine",
        "description": "Please review and approve the medication order.",
        "code_coding": [
            {
                "system": "http://hl7.org/fhir/CodeSystem/task-code",
                "code": "approve",
                "display": "Activate/approve the focal resource",
            }
        ],
        "code_text": "Approve medication request",
        "for": f"Patient/{patient_id}",
        "for_display": "Jane Doe",
        "execution_period_start": "2026-01-01T12:00:00Z",
        "execution_period_end": "2026-01-02T12:00:00Z",
        "authored_on": "2026-01-01T12:00:00Z",
        "last_modified": "2026-01-01T12:00:00Z",
        "status_reason_coding": [
            {
                "system": "http://example.org/status-reason",
                "code": "standard-review",
                "display": "Standard clinical review required",
            }
        ],
        "status_reason_text": "Standard clinical review required",
        "business_status_coding": [
            {
                "system": "http://example.org/business-status",
                "code": "waiting-on-review",
                "display": "Waiting on review",
            }
        ],
        "business_status_text": "Waiting on review",
        "reason_code_coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "182888003",
                "display": "Medication review needed",
            }
        ],
        "reason_code_text": "Medication review needed",
        "performer_type": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                        "code": "RESP",
                        "display": "Responsible Party",
                    }
                ],
                "text": "Responsible Doctor",
            }
        ],
        "note": [
            {
                "author_string": "Nurse Kelly",
                "text": "All vitals checked and normal.",
            }
        ],
        "input": [
            {
                "type_coding": [
                    {
                        "system": "http://example.org/task-input",
                        "code": "specification",
                        "display": "Task Specification",
                    }
                ],
                "type_text": "Task Specification",
                "value_string": "Sample instructions",
            }
        ],
        "output": [
            {
                "type_coding": [
                    {
                        "system": "http://example.org/task-output",
                        "code": "result",
                        "display": "Approval Decision",
                    }
                ],
                "type_text": "Approval Decision",
                "value_string": "Approved by supervisor",
            }
        ],
        "restriction": {
            "repetitions": 1,
            "period_start": "2026-01-01T12:00:00Z",
            "period_end": "2026-01-08T12:00:00Z",
        },
    }

    if encounter_id:
        payload["encounter"] = f"Encounter/{encounter_id}"
        payload["encounter_display"] = "Outpatient consultation"
    if requester_id:
        payload["requester"] = f"Practitioner/{requester_id}"
        payload["requester_display"] = "Dr. Alice Smith"
    if owner_id:
        payload["owner"] = f"Practitioner/{owner_id}"
        payload["owner_display"] = "Dr. Bob Jones"
    if location_id:
        payload["location"] = f"Location/{location_id}"
        payload["location_display"] = "Examination Room 1"
    if org_id:
        payload["identifier"] = [
            {
                "use": "official",
                "system": "http://example.org/task-ids",
                "value": "TASK-12345",
                "assigner": f"Organization/{org_id}",
                "assigner_display": "Good Health Clinic",
            }
        ]
        payload["group_identifier_use"] = "official"
        payload["group_identifier_system"] = "http://example.org/group-ids"
        payload["group_identifier_value"] = "GRP-999"
        payload["group_identifier_assigner"] = f"Organization/{org_id}"
        payload["group_identifier_assigner_display"] = "Good Health Clinic"

    return payload
