"""FHIR R4 conformance for `to_fhir_communication()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Communication is stored content-based (like Task, Goal, Consent and the other rebuilt resources):
the resource lives whole in CommunicationModel.content, and to_fhir_communication() only stamps
`id` and `meta` onto it. So what can go wrong on the read side is that stamping (e.g. a malformed
meta extension) or a stored document the server returns that isn't valid R4 - each case below is a
`content` document as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.communication import to_fhir_communication
from app.models.communication import CommunicationModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.communication_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
CATEGORY = "http://terminology.hl7.org/CodeSystem/communication-category"
BASE = {"status": "completed"}


def _comm(content: dict, **overrides) -> CommunicationModel:
    fields = {
        "communication_id": 480001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return CommunicationModel(**fields)


def _c(**extra) -> CommunicationModel:
    return _comm({**BASE, **extra})


CASES = {
    "minimal": _comm(BASE),
    "updated_by_and_updated_at": _comm(BASE, updated_by="u-other", updated_at=D),
    **{
        f"status_{s}": _c(status=s)
        for s in (
            "preparation",
            "in-progress",
            "not-done",
            "on-hold",
            "stopped",
            "completed",
            "entered-in-error",
            "unknown",
        )
    },
    **{f"priority_{p}": _c(priority=p) for p in ("routine", "urgent", "asap", "stat")},
    "identifier_with_type_and_assigner": _c(
        identifier=[
            {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "FILL",
                        }
                    ]
                },
                "system": "https://fhir-server.dev/fhir/identifier-system/communication-id",
                "value": "CM-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "instantiates": _c(
        instantiatesCanonical=["http://example.org/PlanDefinition/x|1.0"],
        instantiatesUri=["http://example.org/protocols/x", "http://example.org/y"],
    ),
    "based_on_and_part_of_any_type": _c(
        basedOn=[
            {"reference": "ServiceRequest/80001"},
            {"reference": "Device/7"},
            {"reference": "https://other.example.org/fhir/CarePlan/9"},
        ],
        partOf=[{"reference": "Communication/480000"}],
    ),
    "in_response_to": _c(inResponseTo=[{"reference": "Communication/480000"}]),
    "status_reason": _c(statusReason={"text": "no answer"}),
    "category_and_medium": _c(
        category=[{"coding": [{"system": CATEGORY, "code": "alert"}]}, {"text": "x"}],
        medium=[{"text": "written"}, {"coding": [{"system": "http://x", "code": "W"}]}],
    ),
    "subject_patient": _c(subject={"reference": "Patient/10001"}),
    "subject_group": _c(subject={"reference": "Group/430001"}),
    "subject_logical": _c(
        subject={"identifier": {"system": "urn:mrn", "value": "M-9"}, "display": "Jane"}
    ),
    "topic_about_encounter": _c(
        topic={"text": "results"},
        about=[{"reference": "Observation/160001"}],
        encounter={"reference": "Encounter/20001"},
    ),
    "sent_and_received": _c(
        sent="2026-01-15T09:00:00Z", received="2026-01-15T09:05:00Z"
    ),
    "sent_partial": _c(sent="2026-01"),
    "recipient_and_sender": _c(
        recipient=[
            {"reference": "Patient/10001"},
            {"reference": "Group/430001"},
            {"reference": "CareTeam/390001"},
        ],
        sender={"reference": "Practitioner/30001"},
    ),
    "reason": _c(
        reasonCode=[{"text": "results ready"}],
        reasonReference=[{"reference": "Condition/120001"}],
    ),
    "payload_choices": _c(
        payload=[
            {"contentString": "Your results are ready."},
            {"contentAttachment": {"contentType": "application/pdf", "title": "r"}},
            {"contentReference": {"reference": "DocumentReference/320001"}},
        ]
    ),
    "note": _c(
        note=[
            {"text": "Sent by post", "time": "2026-01-15T09:00:00Z"},
            {
                "text": "by a person",
                "authorReference": {"reference": "Practitioner/30001"},
            },
        ]
    ),
    "extension": _c(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full": _c(
        identifier=[{"system": "urn:c", "value": "CM-1"}],
        category=[{"text": "alert"}],
        priority="urgent",
        subject={"reference": "Patient/10001"},
        encounter={"reference": "Encounter/20001"},
        sent="2026-01-15T09:00:00Z",
        recipient=[{"reference": "Patient/10001"}],
        sender={"reference": "Practitioner/30001"},
        payload=[{"contentString": "hello"}],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_communication_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.Communication, to_fhir_communication(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {**BASE, "priority": "stat", "sent": "2026-01-15"}
    out = to_fhir_communication(_comm(content))
    assert out["resourceType"] == "Communication"
    assert out["id"] == "480001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `subject`, `sender` or `topic` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("priority with an unknown code", {"priority": "now"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("instantiatesCanonical as string", {"instantiatesCanonical": "http://x"}),
        ("instantiatesUri entry as number", {"instantiatesUri": [5]}),
        (
            "basedOn as object not a list",
            {"basedOn": {"reference": "ServiceRequest/1"}},
        ),
        ("partOf as string", {"partOf": "Communication/1"}),
        ("inResponseTo as object", {"inResponseTo": {"reference": "Communication/1"}}),
        ("statusReason as string", {"statusReason": "x"}),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("medium as string", {"medium": "x"}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        ("topic as string", {"topic": "x"}),
        ("encounter as string", {"encounter": "Encounter/1"}),
        ("sent not a dateTime", {"sent": "yesterday"}),
        ("received as number", {"received": 5}),
        ("recipient as object not a list", {"recipient": {"reference": "Patient/1"}}),
        ("sender as string", {"sender": "Practitioner/1"}),
        ("reasonCode as object", {"reasonCode": {"text": "x"}}),
        ("payload as object not a list", {"payload": {"contentString": "x"}}),
        ("payload contentString as number", {"payload": [{"contentString": 5}]}),
        (
            "payload contentReference as string",
            {"payload": [{"contentReference": "Patient/1"}]},
        ),
        ("note as string", {"note": "x"}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Communication", "id": "480001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.Communication, validate=True
        )
