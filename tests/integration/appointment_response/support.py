"""Shared helpers and payloads for appointment_response integration tests.

Request bodies are genuine FHIR R4 AppointmentResponse JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

# The resources an AppointmentResponse points at are created through their own routers.
from tests.integration.appointment.support import (  # noqa: F401
    appointment_body,
    create_appointment,
    create_healthcare_service,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    participant,
)

BASE = "/api/fhir/v1/appointment-responses"
API = "/api/fhir/v1"

AR_IDS = "https://fhir-server.dev/fhir/identifier-system/appointment-response-id"

START = "2026-06-01T09:00:00Z"
END = "2026-06-01T09:30:00Z"


def response_body(appointment_id: int | None = None, actor: str | None = None, status: str = "accepted", **extra) -> dict:
    """A valid minimal AppointmentResponse: R4 requires `appointment` and
    `participantStatus`, and (apr-1) `participantType` or `actor`. With no
    appointment the reference is an absolute URL (not existence-checked); with
    no actor, a `participantType` stands in for apr-1."""
    body = {
        "appointment": {"reference": f"Appointment/{appointment_id}" if appointment_id else "https://other.example.org/fhir/Appointment/1"},
        "participantStatus": status,
    }
    if actor:
        body["actor"] = {"reference": actor}
    else:
        body["participantType"] = [{"text": "interpreter"}]
    body.update(extra)
    return body


def full_body(appointment_id: int, patient_id: int) -> dict:
    return {
        "resourceType": "AppointmentResponse",
        "identifier": [
            {
                "system": AR_IDS,
                "value": "AR-1001",
                "assigner": {"identifier": {"system": "urn:external-registry", "value": "EXTERNAL-1"}},
            }
        ],
        "appointment": {"reference": f"Appointment/{appointment_id}"},
        "start": START,
        "end": END,
        "participantType": [{"coding": [{"code": "ATND"}], "text": "attendee"}],
        "actor": {"reference": f"Patient/{patient_id}", "display": "A. Patient"},
        "participantStatus": "tentative",
        "comment": "Might be a few minutes late",
    }


async def create_response(client, body: dict) -> int:
    """Create an appointment response and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
