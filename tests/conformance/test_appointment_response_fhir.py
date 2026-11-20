"""FHIR R4 conformance for `to_fhir_appointment_response()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

AppointmentResponse is stored Medplum-style (like Appointment, Slot, Patient and
the other content-based resources): the resource lives whole in
AppointmentResponseModel.content, and to_fhir_appointment_response() only stamps
`id` and `meta` onto it. So what can go wrong on the read side is that stamping
(e.g. a malformed meta extension) or a stored document the server returns that
isn't valid R4 — each case below is a `content` document as the write path would
store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.appointment_response import to_fhir_appointment_response
from app.models.appointment_response import AppointmentResponseModel

from .support import assert_valid, fhir_json_text

appointment_response_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.appointment_response_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
APPOINTMENT = {"reference": "Appointment/40001"}
ACTOR = {"reference": "Patient/10001"}


def _response(content: dict, **overrides) -> AppointmentResponseModel:
    fields = {
        "appointment_response_id": 370001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return AppointmentResponseModel(**fields)


def _with(**elements) -> AppointmentResponseModel:
    return _response({"appointment": APPOINTMENT, "participantStatus": "accepted", "actor": ACTOR, **elements})


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _response(
        {"appointment": APPOINTMENT, "participantStatus": "accepted", "actor": ACTOR},
        updated_by="u-other",
        updated_at=D,
    ),
    **{f"status_{s}": _with(participantStatus=s) for s in ("accepted", "declined", "tentative", "needs-action")},
    "identifier_with_type_and_assigner": _with(
        identifier=[
            {
                "use": "official",
                "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "VN"}]},
                "system": "http://hospital.example.org/appointment-responses",
                "value": "AR-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "start_and_end": _with(start="2026-06-01T09:00:00Z", end="2026-06-01T09:30:00Z"),
    "start_with_offset": _with(start="2026-06-01T09:00:00+02:00"),
    "participant_type": _with(participantType=[{"coding": [{"code": "ATND", "display": "attender"}], "text": "attendee"}]),
    "participant_type_only_no_actor": _response(
        {"appointment": APPOINTMENT, "participantStatus": "tentative", "participantType": [{"text": "interpreter"}]}
    ),
    "several_participant_types": _with(participantType=[{"coding": [{"code": "ATND"}]}, {"coding": [{"code": "TRANS"}]}]),
    "comment": _with(comment="Might be late"),
    "actor_with_display": _with(actor={"reference": "Practitioner/30001", "display": "Dr Careful"}),
    "actor_logical": _with(actor={"identifier": {"system": "urn:pts", "value": "P-9"}, "display": "Ext"}),
    "appointment_absolute_url": _with(appointment={"reference": "https://other.example.org/fhir/Appointment/9"}),
    "appointment_logical": _with(appointment={"identifier": {"system": "urn:appts", "value": "A-9"}}),
    "extension": _with(extension=[{"url": "https://fhir-server.dev/fhir/StructureDefinition/x", "valueString": "y"}]),
    "full": _with(
        identifier=[{"system": "urn:ar", "value": "AR-1"}],
        start="2026-06-01T09:00:00Z",
        end="2026-06-01T09:30:00Z",
        participantType=[{"text": "attendee"}],
        participantStatus="declined",
        comment="c",
    ),
}
CASES.update(
    {
        f"actor_{t}": _with(actor={"reference": f"{t}/{i}"})
        for i, t in enumerate(
            ("Patient", "Practitioner", "PractitionerRole", "RelatedPerson", "Device", "HealthcareService", "Location"), 1
        )
    }
)


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_appointment_response_mapper_emits_valid_fhir_r4(case):
    assert_valid(appointment_response_pb2.AppointmentResponse, to_fhir_appointment_response(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {"appointment": APPOINTMENT, "participantStatus": "accepted", "actor": ACTOR, "comment": "c"}
    out = to_fhir_appointment_response(_response(content))
    assert out["resourceType"] == "AppointmentResponse"
    assert out["id"] == "370001"
    assert {k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")} == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1, and an unknown code for `participantStatus` — the
# integration tests cover those.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"comentt": "x"}),
        ("start not an instant", {"start": "tomorrow"}),
        ("end as number", {"end": 5}),
        ("comment as number", {"comment": 5}),
        ("appointment as string not a Reference", {"appointment": "Appointment/1"}),
        ("actor as list", {"actor": [{"reference": "Patient/1"}]}),
        ("participantType as object not a list", {"participantType": {"text": "x"}}),
        ("participantType as string", {"participantType": ["ATND"]}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("participantStatus as number", {"participantStatus": 1}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "AppointmentResponse",
        "id": "370001",
        "appointment": APPOINTMENT,
        "participantStatus": "accepted",
        "actor": ACTOR,
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), appointment_response_pb2.AppointmentResponse, validate=True
        )
