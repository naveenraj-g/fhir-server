"""FHIR R4 conformance for `to_fhir_communication_request()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

CommunicationRequest is stored content-based (like Communication, Task, Goal and the other rebuilt
resources): the resource lives whole in CommunicationRequestModel.content, and
to_fhir_communication_request() only stamps `id` and `meta` onto it. So what can go wrong on the
read side is that stamping (e.g. a malformed meta extension) or a stored document the server
returns that isn't valid R4 - each case below is a `content` document as the write path would
store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.communication_request import to_fhir_communication_request
from app.models.communication_request import CommunicationRequestModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.communication_request_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
CATEGORY = "http://terminology.hl7.org/CodeSystem/communication-category"
BASE = {"status": "active"}


def _request(content: dict, **overrides) -> CommunicationRequestModel:
    fields = {
        "communication_request_id": 470001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return CommunicationRequestModel(**fields)


def _c(**extra) -> CommunicationRequestModel:
    return _request({**BASE, **extra})


CASES = {
    "minimal": _request(BASE),
    "updated_by_and_updated_at": _request(BASE, updated_by="u-other", updated_at=D),
    **{
        f"status_{s}": _c(status=s)
        for s in (
            "draft",
            "active",
            "on-hold",
            "revoked",
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
                "system": "https://fhir-server.dev/fhir/identifier-system/communication-request-id",
                "value": "CR-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "group_identifier": _c(groupIdentifier={"system": "urn:groups", "value": "G-1"}),
    "based_on_any_type": _c(
        basedOn=[
            {"reference": "ServiceRequest/80001"},
            {"reference": "Device/7"},
            {"reference": "https://other.example.org/fhir/CarePlan/9"},
        ]
    ),
    "replaces": _c(replaces=[{"reference": "CommunicationRequest/470000"}]),
    "status_reason": _c(statusReason={"text": "approved"}),
    "do_not_perform": _c(doNotPerform=True),
    "category_and_medium": _c(
        category=[{"coding": [{"system": CATEGORY, "code": "alert"}]}, {"text": "x"}],
        medium=[{"text": "written"}, {"coding": [{"system": "http://x", "code": "W"}]}],
    ),
    "subject_patient": _c(subject={"reference": "Patient/10001"}),
    "subject_group": _c(subject={"reference": "Group/430001"}),
    "subject_logical": _c(
        subject={"identifier": {"system": "urn:mrn", "value": "M-9"}, "display": "Jane"}
    ),
    "about_and_encounter": _c(
        about=[{"reference": "Observation/160001"}],
        encounter={"reference": "Encounter/20001"},
    ),
    "occurrence_datetime": _c(occurrenceDateTime="2026-02-01T09:00:00Z"),
    "occurrence_period": _c(
        occurrencePeriod={"start": "2026-02-01", "end": "2026-02-28"}
    ),
    "authored_on": _c(authoredOn="2026-01-15T09:00:00Z"),
    "authored_on_partial": _c(authoredOn="2026-01"),
    "requester_recipient_and_sender": _c(
        requester={"reference": "Practitioner/30001"},
        recipient=[
            {"reference": "Patient/10001"},
            {"reference": "Group/430001"},
            {"reference": "CareTeam/390001"},
        ],
        sender={"reference": "Practitioner/30001"},
    ),
    "reason": _c(
        reasonCode=[{"text": "follow-up needed"}],
        reasonReference=[{"reference": "Condition/120001"}],
    ),
    "payload_choices": _c(
        payload=[
            {"contentString": "Please book your visit."},
            {"contentAttachment": {"contentType": "application/pdf", "title": "r"}},
            {"contentReference": {"reference": "DocumentReference/320001"}},
        ]
    ),
    "note": _c(
        note=[
            {"text": "Call twice", "time": "2026-01-15T09:00:00Z"},
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
        identifier=[{"system": "urn:c", "value": "CR-1"}],
        category=[{"text": "alert"}],
        priority="urgent",
        subject={"reference": "Patient/10001"},
        encounter={"reference": "Encounter/20001"},
        occurrenceDateTime="2026-02-01T09:00:00Z",
        authoredOn="2026-01-15T09:00:00Z",
        requester={"reference": "Practitioner/30001"},
        recipient=[{"reference": "Patient/10001"}],
        sender={"reference": "Practitioner/30001"},
        payload=[{"contentString": "hello"}],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_communication_request_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.CommunicationRequest, to_fhir_communication_request(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {**BASE, "priority": "stat", "authoredOn": "2026-01-15"}
    out = to_fhir_communication_request(_request(content))
    assert out["resourceType"] == "CommunicationRequest"
    assert out["id"] == "470001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `subject`, `requester` or `sender` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("priority with an unknown code", {"priority": "now"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("groupIdentifier as string", {"groupIdentifier": "G-1"}),
        (
            "basedOn as object not a list",
            {"basedOn": {"reference": "ServiceRequest/1"}},
        ),
        ("replaces as string", {"replaces": "CommunicationRequest/1"}),
        ("statusReason as string", {"statusReason": "x"}),
        ("doNotPerform as string", {"doNotPerform": "maybe"}),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("medium as string", {"medium": "x"}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        ("encounter as string", {"encounter": "Encounter/1"}),
        ("occurrenceDateTime not a dateTime", {"occurrenceDateTime": "tomorrow"}),
        ("occurrencePeriod as string", {"occurrencePeriod": "soon"}),
        ("authoredOn not a dateTime", {"authoredOn": "yesterday"}),
        ("requester as string", {"requester": "Practitioner/1"}),
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

    payload = {"resourceType": "CommunicationRequest", "id": "470001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.CommunicationRequest, validate=True
        )
