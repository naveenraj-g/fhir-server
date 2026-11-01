"""Shared helpers and payloads for communication integration tests."""

BASE = "/api/fhir/v1/communications"
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


def minimal_communication(patient_id: int) -> dict:
    return {
        "status": "completed",
        "subject": f"Patient/{patient_id}",
        "subject_display": "Jane Doe",
    }


def full_communication(
    patient_id: int,
    practitioner_id: int,
    organization_id: int,
    encounter_id: int,
    condition_id: int,
) -> dict:
    return {
        "status": "completed",
        "status_reason_text": "Patient confirmed receipt",
        "status_reason_coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/communication-not-done-reason",
                "code": "unknown",
                "display": "Unknown",
            }
        ],
        "priority": "routine",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/communication-category",
                        "code": "notification",
                        "display": "Notification",
                    }
                ],
                "text": "Notification",
            }
        ],
        "medium": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationMode",
                        "code": "WRITTEN",
                        "display": "written",
                    }
                ],
                "text": "written",
            }
        ],
        "subject": f"Patient/{patient_id}",
        "subject_display": "Jane Doe",
        "topic_text": "Annual Wellness Visit Follow-up",
        "topic_coding": [
            {
                "system": "http://example.org/topics",
                "code": "wellness",
                "display": "Wellness",
            }
        ],
        "about": [
            {
                "reference": f"Condition/{condition_id}",
                "display": "Patient condition",
            }
        ],
        "encounter": f"Encounter/{encounter_id}",
        "encounter_display": "Office Visit",
        "sent": "2026-11-01T08:00:00Z",
        "received": "2026-11-01T08:01:00Z",
        "recipient": [
            {
                "reference": f"Patient/{patient_id}",
                "display": "Jane Doe",
            }
        ],
        "sender": f"Practitioner/{practitioner_id}",
        "sender_display": "Dr. Smith",
        "reason_code": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "439401001",
                        "display": "Abnormal lab result",
                    }
                ],
                "text": "Abnormal lab result",
            }
        ],
        "reason_reference": [
            {
                "reference": f"Condition/{condition_id}",
                "display": "Patient condition",
            }
        ],
        "payload": [
            {
                "content_string": "Please follow up on heart rate test results.",
            },
            {
                "content_attachment": {
                    "content_type": "text/plain",
                    "data": "SGVsbG8gV29ybGQ=",
                    "title": "Notes attachment",
                }
            },
        ],
        "note": [
            {
                "author_reference": f"Practitioner/{practitioner_id}",
                "author_display": "Dr. Smith",
                "text": "Contacted patient by phone; left voicemail.",
            }
        ],
        "identifier": [
            {
                "use": "official",
                "system": "http://hospital.example.org",
                "value": "COMM-12345",
                "assigner": f"Organization/{organization_id}",
                "assigner_display": "Good Health Clinic",
            }
        ],
        "instantiates_canonical": ["http://example.org/fhir/Questionnaire/example"],
        "instantiates_uri": ["http://example.org/protocols/protocol1"],
    }
