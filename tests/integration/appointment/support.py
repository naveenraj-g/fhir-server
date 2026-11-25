"""Shared helpers and payloads for appointment integration tests.

Request bodies are genuine FHIR R4 Appointment JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

# The resources an Appointment points at are created through their own routers.
from tests.integration.patient.support import create_patient
from tests.integration.practitioner_role.support import (
    create_healthcare_service,
    create_location,
    create_organization,
    create_practitioner,
)
from tests.integration.practitioner_role.support import (
    create_role as create_practitioner_role,
)
from tests.integration.schedule.support import create_schedule
from tests.integration.slot.support import create_slot, slot_body

BASE = "/api/fhir/v1/appointments"
API = "/api/fhir/v1"

APPT_IDS = "https://fhir-server.dev/fhir/identifier-system/appointment-id"
CAT = "http://terminology.hl7.org/CodeSystem/service-category"
TYPE = "http://terminology.hl7.org/CodeSystem/service-type"
APPT = "http://terminology.hl7.org/CodeSystem/v2-0276"
SCT = "http://snomed.info/sct"

START = "2026-06-01T09:00:00Z"
END = "2026-06-01T09:30:00Z"


def participant(actor: str | None = None, status: str = "accepted", **extra) -> dict:
    """One Appointment.participant (R4: `status` is required)."""
    body = {"status": status, **extra}
    if actor:
        body["actor"] = {"reference": actor}
    return body


def appointment_body(patient_id: int | None = None, **changes) -> dict:
    """A valid minimal Appointment: R4 requires `status` and at least one
    participant (each with a `status`). With no patient, the participant is a
    Patient that isn't a row here — an absolute reference isn't existence-checked."""
    actor = (
        f"Patient/{patient_id}"
        if patient_id
        else "https://other.example.org/fhir/Patient/1"
    )
    return {"status": "booked", "participant": [participant(actor)], **changes}


def full_body(
    patient_id: int,
    practitioner_id: int,
    location_id: int,
    slot_id: int,
    condition_id: int,
) -> dict:
    return appointment_body(
        patient_id,
        resourceType="Appointment",
        identifier=[
            {
                "system": APPT_IDS,
                "value": "AP-1001",
                "assigner": {
                    "identifier": {
                        "system": "urn:external-registry",
                        "value": "EXTERNAL-1",
                    }
                },
            }
        ],
        cancelationReason={"text": "Patient unwell"},
        serviceCategory=[
            {
                "coding": [
                    {"system": CAT, "code": "17", "display": "General Practice"}
                ],
                "text": "General",
            }
        ],
        serviceType=[
            {"coding": [{"system": TYPE, "code": "124", "display": "General Practice"}]}
        ],
        specialty=[
            {"coding": [{"system": SCT, "code": "394579002", "display": "Cardiology"}]}
        ],
        appointmentType={
            "coding": [
                {"system": APPT, "code": "ROUTINE", "display": "Routine appointment"}
            ],
            "text": "Routine",
        },
        reasonCode=[
            {
                "coding": [{"system": SCT, "code": "413153004", "display": "Check-up"}],
                "text": "Annual check-up",
            }
        ],
        reasonReference=[{"reference": f"Condition/{condition_id}"}],
        priority=5,
        description="Discussion on the results of the MRI",
        supportingInformation=[{"reference": "Encounter/20001"}],
        start=START,
        end=END,
        minutesDuration=30,
        slot=[{"reference": f"Slot/{slot_id}"}],
        created="2026-05-20T10:00:00Z",
        comment="Further expand on the results of the MRI",
        patientInstruction="Please arrive 15 minutes early",
        basedOn=[{"reference": "ServiceRequest/80001"}],
        participant=[
            participant(
                f"Patient/{patient_id}",
                required="required",
                type=[{"coding": [{"code": "ATND"}], "text": "attendee"}],
                period={"start": START, "end": END},
            ),
            participant(f"Practitioner/{practitioner_id}", required="required"),
            participant(
                f"Location/{location_id}",
                required="information-only",
                status="tentative",
            ),
        ],
        requestedPeriod=[{"start": "2026-06-01", "end": "2026-06-07"}],
    )


async def create_condition(client, patient_id: int | None = None) -> int:
    """A minimal Condition an Appointment / Encounter can name as its reason; with
    no patient the subject is an absolute URL (not existence-checked)."""
    subject = (
        f"Patient/{patient_id}"
        if patient_id
        else "https://other.example.org/fhir/Patient/1"
    )
    resp = await client.post(
        f"{API}/conditions/", json={"subject": {"reference": subject}}
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def create_appointment(client, body: dict) -> int:
    """Create an appointment and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
