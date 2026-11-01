from datetime import datetime, timezone

BASE = "/api/fhir/v1/appointment-responses"
APPOINTMENTS_BASE = "/api/fhir/v1/appointments"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}
PLAIN_ACCEPT = {"Accept": "application/json"}

D = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc).isoformat()
D2 = datetime(2026, 6, 1, 9, 30, tzinfo=timezone.utc).isoformat()


async def create_parent_appointment(client) -> int:
    payload = {
        "status": "booked",
        "start": D,
        "end": D2,
        "participant": [
            {
                "status": "accepted",
                "actor_display": "Dr. Smith",
            }
        ],
    }
    resp = await client.post(APPOINTMENTS_BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def appointment_response_with_fallbacks(appointment_id: int) -> dict:
    return {
        "appointment": f"Appointment/{appointment_id}",
        "appointment_display": "Dr. Smith consultation",
        "participant_status": "accepted",
        "start": D,
        "end": D2,
        "comment": "Confirmed attendance",
        "actor_display": "Dr. External Provider",
        "actor_identifier_system": "http://npi.example.org",
        "actor_identifier_value": "NPI-887766",
        "actor_identifier_use": "official",
        "identifier": [
            {
                "system": "http://replies.example.org",
                "value": "RESP-001",
                "assigner_display": "External Scheduling Service",
                "assigner_identifier_system": "http://agencies.example.org",
                "assigner_identifier_value": "SCHED-AGENCY-9",
                "assigner_identifier_use": "official",
            }
        ],
    }
