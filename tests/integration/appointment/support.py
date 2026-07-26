"""Shared helpers and payloads for appointment integration tests."""

from tests.integration.patient.support import create_patient
from tests.integration.practitioner.support import create_practitioner

BASE = "/api/fhir/v1/appointments"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def build_minimal_payload(client, *, user_id: str = "u-test", org_id: str = "org-test") -> dict:
    """Create prerequisite resources and return a realistic minimal appointment payload."""
    patient_id = await create_patient(client)
    practitioner_id = await create_practitioner(client)
    return {
        "user_id": user_id,
        "org_id": org_id,
        "status": "booked",
        "start": "2026-06-01T09:00:00Z",
        "end": "2026-06-01T09:30:00Z",
        "minutes_duration": 30,
        "description": "Initial consultation",
        "participant": [
            {
                "reference": f"Patient/{patient_id}",
                "reference_display": "Patient Primary",
                "required": "required",
                "status": "accepted",
            },
            {
                "reference": f"Practitioner/{practitioner_id}",
                "reference_display": "Dr. Primary",
                "types": [
                    {
                        "coding_code": "ATND",
                        "coding_display": "attender",
                    }
                ],
                "required": "required",
                "status": "accepted",
            },
        ],
    }


async def build_full_payload(client, *, user_id: str = "u-test", org_id: str = "org-test") -> dict:
    """Return a rich appointment payload that exercises nested mapping behavior."""
    payload = await build_minimal_payload(client, user_id=user_id, org_id=org_id)
    payload.update(
        {
            "cancelation_reason_system": "http://terminology.hl7.org/CodeSystem/appointment-cancellation-reason",
            "cancelation_reason_code": "pat",
            "cancelation_reason_display": "Patient",
            "cancelation_reason_text": "Patient requested reschedule",
            "appointment_type_system": "http://terminology.hl7.org/CodeSystem/v2-0276",
            "appointment_type_code": "FOLLOWUP",
            "appointment_type_display": "Follow-up",
            "appointment_type_text": "Follow-up visit",
            "priority": 5,
            "created": "2026-05-01T08:00:00Z",
            "description": "Telehealth follow-up for ongoing symptoms",
            "comment": "Patient prefers video visits.",
            "patient_instruction": "Log in 10 minutes early",
            "identifier": [
                {
                    "use": "official",
                    "type_system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                    "type_code": "PLAC",
                    "type_display": "Placer Identifier",
                    "type_text": "Internal placer",
                    "system": "urn:appointment",
                    "value": "APT-001",
                    "period_start": "2026-06-01T09:00:00Z",
                    "period_end": "2026-06-30T09:30:00Z",
                    "assigner": "Scheduling Desk",
                }
            ],
            "service_category": [
                {
                    "coding_system": "http://example.org/service-category",
                    "coding_code": "gp",
                    "coding_display": "General practice",
                    "text": "Primary care",
                }
            ],
            "service_type": [
                {
                    "coding_system": "http://example.org/service-type",
                    "coding_code": "tele",
                    "coding_display": "Telehealth",
                    "text": "Video consult",
                }
            ],
            "specialty": [
                {
                    "coding_system": "http://snomed.info/sct",
                    "coding_code": "408443003",
                    "coding_display": "General medical practice",
                    "text": "General practice",
                }
            ],
            "reason_code": [
                {
                    "coding_system": "http://snomed.info/sct",
                    "coding_code": "386661006",
                    "coding_display": "Fever",
                    "text": "Fever follow-up",
                }
            ],
            "reason_reference": [
                {
                    "reference": "Condition/12345",
                    "reference_display": "Fever condition",
                }
            ],
            "supporting_information": [
                {
                    "reference": "DocumentReference/456",
                    "reference_display": "Referral letter",
                }
            ],
            "slot": [
                {
                    "reference": "Slot/501",
                    "reference_display": "Morning telehealth slot",
                }
            ],
            "based_on": [
                {
                    "reference": "ServiceRequest/80001",
                    "reference_display": "Referral request",
                }
            ],
            "requested_period": [
                {
                    "period_start": "2026-06-02T09:00:00Z",
                    "period_end": "2026-06-02T10:00:00Z",
                }
            ],
            "recurrence_template": {
                "recurrence_type_code": "weekly",
                "recurrence_type_display": "Weekly",
                "recurrence_type_system": "http://example.org/recurrence",
                "timezone_code": "Asia/Kolkata",
                "timezone_display": "Asia/Kolkata",
                "last_occurrence_date": "2026-07-01",
                "occurrence_count": 4,
                "occurrence_dates": ["2026-06-01", "2026-06-08"],
                "excluding_dates": ["2026-06-15"],
                "excluding_recurrence_ids": [3],
                "weekly_template": {
                    "monday": True,
                    "week_interval": 1,
                },
            },
        }
    )
    return payload


async def create_appointment(client, payload=None) -> int:
    """Create an appointment and return the public appointment id."""
    payload = payload or await build_minimal_payload(client)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 200
    return resp.json()["id"]
