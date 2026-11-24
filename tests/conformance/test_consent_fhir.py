"""FHIR R4 conformance for `to_fhir_consent()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Consent is stored content-based (like Goal, Task, Flag and the other rebuilt resources): the
resource lives whole in ConsentModel.content, and to_fhir_consent() only stamps `id` and `meta`
onto it. So what can go wrong on the read side is that stamping (e.g. a malformed meta extension)
or a stored document the server returns that isn't valid R4 - each case below is a `content`
document as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.consent import to_fhir_consent
from app.models.consent import ConsentModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.consent_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SCOPE = "http://terminology.hl7.org/CodeSystem/consentscope"
LOINC = "http://loinc.org"
ACTION = "http://terminology.hl7.org/CodeSystem/consentaction"
BASE = {
    "status": "active",
    "scope": {"coding": [{"system": SCOPE, "code": "patient-privacy"}]},
    "category": [{"coding": [{"system": LOINC, "code": "59284-0"}]}],
}


def _consent(content: dict, **overrides) -> ConsentModel:
    fields = {
        "consent_id": 440001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return ConsentModel(**fields)


def _c(**extra) -> ConsentModel:
    return _consent({**BASE, **extra})


CASES = {
    "minimal": _consent(BASE),
    "updated_by_and_updated_at": _consent(BASE, updated_by="u-other", updated_at=D),
    **{
        f"status_{s}": _c(status=s)
        for s in (
            "draft",
            "proposed",
            "active",
            "rejected",
            "inactive",
            "entered-in-error",
        )
    },
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
                "system": "https://fhir-server.dev/fhir/identifier-system/consent-id",
                "value": "C-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "scope_text_only": _c(scope={"text": "privacy"}),
    "several_categories": _c(
        category=[{"text": "a"}, {"coding": [{"system": LOINC, "code": "1"}]}]
    ),
    "patient": _c(patient={"reference": "Patient/10001"}),
    "patient_logical": _c(
        patient={"identifier": {"system": "urn:mrn", "value": "M-9"}, "display": "Jane"}
    ),
    "patient_absolute_url": _c(
        patient={"reference": "https://other.example.org/fhir/Patient/1"}
    ),
    "date_time": _c(dateTime="2026-01-15T09:00:00Z"),
    "date_time_partial": _c(dateTime="2026-01"),
    "performer_and_organization": _c(
        performer=[{"reference": "Patient/10001"}, {"reference": "Practitioner/30001"}],
        organization=[{"reference": "Organization/190001"}],
    ),
    "source_attachment": _c(
        sourceAttachment={"contentType": "application/pdf", "title": "signed"}
    ),
    **{
        f"source_reference_{t.lower()}": _c(sourceReference={"reference": f"{t}/1"})
        for t in ("Consent", "DocumentReference", "Contract", "QuestionnaireResponse")
    },
    "policy": _c(
        policy=[
            {"authority": "urn:authority", "uri": "http://example.org/policy"},
            {"uri": "http://example.org/other"},
        ]
    ),
    "policy_rule": _c(
        policyRule={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "OPTIN",
                }
            ]
        }
    ),
    "verification": _c(
        verification=[
            {
                "verified": True,
                "verifiedWith": {"reference": "Patient/10001"},
                "verificationDate": "2026-01-16T10:00:00Z",
            },
            {"verified": False},
        ]
    ),
    "provision": _c(
        provision={
            "type": "permit",
            "period": {"start": "2026-01-15", "end": "2027-01-14"},
            "actor": [
                {
                    "role": {"coding": [{"system": SCOPE, "code": "x"}]},
                    "reference": {"reference": "Practitioner/30001"},
                }
            ],
            "action": [{"coding": [{"system": ACTION, "code": "access"}]}],
            "securityLabel": [{"system": "http://example.org/sl", "code": "R"}],
            "purpose": [{"system": "http://example.org/p", "code": "TREAT"}],
            "class": [
                {"system": "http://hl7.org/fhir/resource-types", "code": "Observation"}
            ],
            "code": [{"text": "vitals"}],
            "dataPeriod": {"start": "2025-01-01", "end": "2025-12-31"},
            "data": [
                {
                    "meaning": "instance",
                    "reference": {"reference": "Observation/160001"},
                },
                {"meaning": "related", "reference": {"reference": "Device/9"}},
            ],
        }
    ),
    "provision_deny": _c(provision={"type": "deny"}),
    "nested_provisions": _c(
        provision={
            "type": "permit",
            "provision": [
                {
                    "type": "deny",
                    "actor": [
                        {
                            "role": {"text": "r"},
                            "reference": {"reference": "Organization/190001"},
                        }
                    ],
                    "provision": [{"type": "permit", "action": [{"text": "access"}]}],
                }
            ],
        }
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
        identifier=[{"system": "urn:c", "value": "C-1"}],
        patient={"reference": "Patient/10001"},
        dateTime="2026-01-15T09:00:00Z",
        performer=[{"reference": "Patient/10001"}],
        organization=[{"reference": "Organization/190001"}],
        sourceReference={"reference": "DocumentReference/320001"},
        policyRule={"text": "opt in"},
        provision={"type": "permit", "period": {"start": "2026-01-15"}},
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_consent_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.Consent, to_fhir_consent(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {**BASE, "dateTime": "2026-01-15"}
    out = to_fhir_consent(_consent(content))
    assert out["resourceType"] == "Consent"
    assert out["id"] == "440001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `scope`, `patient` or `provision` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("scope as string", {"scope": "patient-privacy"}),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("patient as string not a Reference", {"patient": "Patient/1"}),
        ("dateTime not a dateTime", {"dateTime": "yesterday"}),
        ("performer as object not a list", {"performer": {"reference": "Patient/1"}}),
        ("organization as string", {"organization": "Organization/1"}),
        ("sourceReference as string", {"sourceReference": "Consent/1"}),
        ("policy as object not a list", {"policy": {"uri": "x"}}),
        ("policy uri as number", {"policy": [{"uri": 5}]}),
        ("policyRule as string", {"policyRule": "x"}),
        ("verification verified as string", {"verification": [{"verified": "yes"}]}),
        ("provision type unknown code", {"provision": {"type": "maybe"}}),
        ("provision period as string", {"provision": {"period": "now"}}),
        (
            "provision actor as object",
            {"provision": {"actor": {"role": {"text": "x"}}}},
        ),
        (
            "provision data meaning unknown code",
            {"provision": {"data": [{"meaning": "everything"}]}},
        ),
        ("provision securityLabel as string", {"provision": {"securityLabel": ["R"]}}),
        ("nested provision as object", {"provision": {"provision": {"type": "deny"}}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Consent", "id": "440001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.Consent, validate=True
        )
