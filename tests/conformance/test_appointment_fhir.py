"""FHIR R4 conformance for `to_fhir_appointment()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Appointment is stored Medplum-style (like Slot, Patient and the other
content-based resources): the resource lives whole in AppointmentModel.content,
and to_fhir_appointment() only stamps `id` and `meta` onto it. So what can go
wrong on the read side is that stamping (e.g. a malformed meta extension) or a
stored document the server returns that isn't valid R4 — each case below is a
`content` document as the write path would store it, run through the real read
mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.appointment import to_fhir_appointment
from app.models.appointment import AppointmentModel

from .support import assert_valid, fhir_json_text

appointment_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.appointment_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
PART = {"actor": {"reference": "Patient/10001"}, "status": "accepted"}


def _appointment(content: dict, **overrides) -> AppointmentModel:
    fields = {
        "appointment_id": 40001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return AppointmentModel(**fields)


def _with(**elements) -> AppointmentModel:
    return _appointment({"status": "booked", "participant": [PART], **elements})


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _appointment(
        {"status": "booked", "participant": [PART]}, updated_by="u-other", updated_at=D
    ),
    **{
        f"status_{s}": _with(status=s)
        for s in (
            "proposed",
            "pending",
            "booked",
            "arrived",
            "fulfilled",
            "cancelled",
            "noshow",
            "entered-in-error",
            "checked-in",
            "waitlist",
        )
    },
    "identifier_with_type_and_assigner": _with(
        identifier=[
            {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "VN",
                        }
                    ]
                },
                "system": "http://hospital.example.org/appointments",
                "value": "AP-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "cancelation_reason": _with(
        status="cancelled",
        cancelationReason={
            "coding": [{"code": "pat", "display": "Patient"}],
            "text": "Patient unwell",
        },
    ),
    "service_category": _with(
        serviceCategory=[
            {"coding": [{"code": "17", "display": "General Practice"}], "text": "GP"}
        ]
    ),
    "service_type": _with(serviceType=[{"coding": [{"code": "124"}]}]),
    "specialty": _with(
        specialty=[{"coding": [{"code": "394579002", "display": "Cardiology"}]}]
    ),
    "appointment_type": _with(
        appointmentType={
            "coding": [{"code": "ROUTINE", "display": "Routine appointment"}]
        }
    ),
    "reason_code": _with(
        reasonCode=[{"coding": [{"code": "413153004"}], "text": "Check-up"}]
    ),
    "reason_references_of_every_type": _with(
        reasonReference=[
            {"reference": "Condition/120001"},
            {"reference": "Observation/160001"},
            {"reference": "Procedure/100001"},
            {"reference": "ImmunizationRecommendation/510001"},
        ]
    ),
    "priority_and_description": _with(
        priority=5, description="Discussion on the results of your MRI"
    ),
    "supporting_information": _with(
        supportingInformation=[
            {"reference": "Encounter/20001"},
            {"reference": "https://other.example.org/fhir/Patient/9"},
        ]
    ),
    "start_end_duration": _with(
        start="2026-06-01T09:00:00Z", end="2026-06-01T09:30:00Z", minutesDuration=30
    ),
    "start_with_offset": _with(start="2026-06-01T09:00:00+02:00"),
    "slots": _with(slot=[{"reference": "Slot/220001"}, {"reference": "Slot/220002"}]),
    "created_comment_instruction": _with(
        created="2026-05-20T10:00:00Z",
        comment="Bring reports",
        patientInstruction="Arrive early",
    ),
    "based_on": _with(basedOn=[{"reference": "ServiceRequest/80001"}]),
    "participants_of_every_actor_type": _with(
        participant=[
            {"actor": {"reference": f"{t}/{i}"}, "status": "accepted"}
            for i, t in enumerate(
                (
                    "Patient",
                    "Practitioner",
                    "PractitionerRole",
                    "RelatedPerson",
                    "Device",
                    "HealthcareService",
                    "Location",
                ),
                1,
            )
        ]
    ),
    "participant_with_every_part": _with(
        participant=[
            {
                "type": [{"coding": [{"code": "ATND"}], "text": "attendee"}],
                "actor": {"reference": "Practitioner/30001", "display": "Dr Careful"},
                "required": "information-only",
                "status": "needs-action",
                "period": {
                    "start": "2026-06-01T09:00:00Z",
                    "end": "2026-06-01T09:30:00Z",
                },
            }
        ]
    ),
    "participant_with_only_a_type": _with(
        participant=[{"type": [{"text": "interpreter"}], "status": "tentative"}]
    ),
    "participant_logical_actor": _with(
        participant=[
            {
                "actor": {
                    "identifier": {"system": "urn:pts", "value": "P-9"},
                    "display": "Ext",
                },
                "status": "declined",
            }
        ]
    ),
    "every_participation_status_and_required": _with(
        participant=[
            {"actor": {"reference": "Patient/1"}, "required": r, "status": s}
            for r, s in (
                ("required", "accepted"),
                ("optional", "declined"),
                ("information-only", "tentative"),
                ("required", "needs-action"),
            )
        ]
    ),
    "requested_periods": _with(
        requestedPeriod=[
            {"start": "2026-06-01", "end": "2026-06-07"},
            {"start": "2026-07-01"},
        ]
    ),
    "extension": _with(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full": _with(
        identifier=[{"system": "urn:ap", "value": "AP-1"}],
        serviceCategory=[{"text": "GP"}],
        appointmentType={"text": "Routine"},
        reasonCode=[{"text": "Check-up"}],
        priority=1,
        description="d",
        start="2026-06-01T09:00:00Z",
        end="2026-06-01T09:30:00Z",
        minutesDuration=30,
        slot=[{"reference": "Slot/220001"}],
        created="2026-05-20",
        comment="c",
        patientInstruction="i",
        requestedPeriod=[{"start": "2026-06-01"}],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_appointment_mapper_emits_valid_fhir_r4(case):
    assert_valid(appointment_pb2.Appointment, to_fhir_appointment(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {"status": "booked", "participant": [PART], "comment": "c", "priority": 2}
    out = to_fhir_appointment(_appointment(content))
    assert out["resourceType"] == "Appointment"
    assert out["id"] == "40001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1, and an unknown code for `status` / `participant.status` /
# `participant.required` — the integration tests cover those.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"descripton": "x"}),
        ("start not an instant", {"start": "tomorrow"}),
        ("priority as string", {"priority": "high"}),
        ("minutesDuration as string", {"minutesDuration": "thirty"}),
        ("comment as number", {"comment": 5}),
        ("slot as strings not References", {"slot": ["Slot/1"]}),
        ("basedOn as string not a list", {"basedOn": "ServiceRequest/1"}),
        (
            "appointmentType as string not CodeableConcept",
            {"appointmentType": "ROUTINE"},
        ),
        ("serviceCategory as object not a list", {"serviceCategory": {"text": "x"}}),
        ("participant as object not a list", {"participant": {"status": "accepted"}}),
        ("requestedPeriod as strings", {"requestedPeriod": ["2026-06-01"]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Appointment",
        "id": "40001",
        "status": "booked",
        "participant": [PART],
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), appointment_pb2.Appointment, validate=True
        )
