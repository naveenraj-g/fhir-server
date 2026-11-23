"""FHIR R4 conformance for `to_fhir_document_reference()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

DocumentReference is stored Medplum-style (like CareTeam, CarePlan, Encounter and the other
content-based resources): the resource lives whole in DocumentReferenceModel.content, and
to_fhir_document_reference() only stamps `id` and `meta` onto it. So what can go wrong on the read
side is that stamping (e.g. a malformed meta extension) or a stored document the server returns
that isn't valid R4 - each case below is a `content` document as the write path would store it,
run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.document_reference import to_fhir_document_reference
from app.models.document_reference import DocumentReferenceModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.document_reference_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
LOINC = "http://loinc.org"
TYPE = {"coding": [{"system": LOINC, "code": "34133-9", "display": "Episode note"}]}
CONTENT = [
    {
        "attachment": {
            "contentType": "application/pdf",
            "url": "https://d.example.org/a.pdf",
        }
    }
]


def _c(content: dict, **overrides) -> DocumentReferenceModel:
    fields = {
        "document_reference_id": 320001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return DocumentReferenceModel(**fields)


def _base(**extra) -> dict:
    return {"status": "current", "content": CONTENT, **extra}


CASES = {
    "minimal": _c(_base()),
    "updated_by_and_updated_at": _c(_base(), updated_by="u-other", updated_at=D),
    "master_identifier_and_identifier": _c(
        _base(
            masterIdentifier={"system": "urn:ietf:rfc:3986", "value": "urn:oid:1.2.3"},
            identifier=[
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "ACSN",
                            }
                        ]
                    },
                    "system": "https://fhir-server.dev/fhir/identifier-system/document-reference-id",
                    "value": "DOC-1",
                    "period": {"start": "2020-01-01"},
                    "assigner": {"reference": "Organization/190001"},
                }
            ],
        )
    ),
    **{
        f"status_{s}": _c(_base(status=s))
        for s in ("current", "superseded", "entered-in-error")
    },
    **{
        f"doc_status_{s}": _c(_base(docStatus=s))
        for s in ("preliminary", "final", "amended", "entered-in-error")
    },
    "type_and_category": _c(
        _base(
            type=TYPE,
            category=[
                {"coding": [{"system": LOINC, "code": "LP173421-1"}]},
                {"text": "Free text category"},
            ],
        )
    ),
    "subject_patient": _c(_base(subject={"reference": "Patient/10001"})),
    "subject_group": _c(_base(subject={"reference": "Group/430001"})),
    "subject_absolute_url": _c(
        _base(subject={"reference": "https://other.example.org/fhir/Patient/1"})
    ),
    "subject_logical_identifier": _c(
        _base(subject={"identifier": {"system": "urn:mrn", "value": "M-1"}})
    ),
    "date": _c(_base(date="2026-02-01T10:00:00Z")),
    "authors": _c(
        _base(
            author=[
                {"reference": "Practitioner/30001"},
                {"reference": "PractitionerRole/140001"},
                {"reference": "Organization/190001", "display": "Providing Org"},
                {"reference": "Device/12"},
            ],
            authenticator={"reference": "Practitioner/30001"},
            custodian={"reference": "Organization/190001"},
        )
    ),
    "relates_to": _c(
        _base(
            relatesTo=[
                {
                    "code": "replaces",
                    "target": {"reference": "DocumentReference/320002"},
                },
                {
                    "code": "appends",
                    "target": {"reference": "DocumentReference/320003"},
                },
            ]
        )
    ),
    "description_and_security_label": _c(
        _base(
            description="Discharge summary",
            securityLabel=[
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                            "code": "N",
                        }
                    ]
                }
            ],
        )
    ),
    "content_with_format": _c(
        {
            "status": "current",
            "content": [
                {
                    "attachment": {
                        "contentType": "application/pdf",
                        "url": "https://d.example.org/a.pdf",
                        "size": 1234,
                        "title": "Discharge summary",
                        "creation": "2026-02-01",
                    },
                    "format": {
                        "system": "http://ihe.net/fhir/ValueSet/IHE.FormatCode.codesystem",
                        "code": "urn:ihe:pcc:handp:2008",
                    },
                },
                {"attachment": {"contentType": "text/plain", "data": "SGVsbG8="}},
            ],
        }
    ),
    "context": _c(
        _base(
            context={
                "encounter": [
                    {"reference": "Encounter/20001"},
                    {"reference": "EpisodeOfCare/350001"},
                ],
                "event": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                                "code": "AMB",
                            }
                        ]
                    }
                ],
                "period": {"start": "2026-01-30", "end": "2026-02-01"},
                "facilityType": {
                    "coding": [{"system": "http://snomed.info/sct", "code": "22232009"}]
                },
                "practiceSetting": {
                    "coding": [
                        {"system": "http://snomed.info/sct", "code": "408443003"}
                    ]
                },
                "sourcePatientInfo": {"reference": "Patient/10001"},
                "related": [
                    {"reference": "Condition/120001"},
                    {"reference": "https://other.example.org/fhir/Task/3"},
                ],
            }
        )
    ),
    "context_period_open": _c(_base(context={"period": {"start": "2026-01-30"}})),
    "extension": _c(
        _base(extension=[{"url": "http://example.org/ext", "valueString": "kept"}])
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_document_reference_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.DocumentReference, to_fhir_document_reference(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _base(description="Discharge summary", type=TYPE)
    out = to_fhir_document_reference(_c(content))
    assert out["resourceType"] == "DocumentReference"
    assert out["id"] == "320001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `subject` or `type` as a one-item list; the integration
# tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "retired"}),
        ("status as number", {"status": 1}),
        ("docStatus with an unknown code", {"docStatus": "draft"}),
        ("type as string", {"type": "x"}),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("category entry as string", {"category": ["x"]}),
        ("subject as string", {"subject": "Patient/1"}),
        ("date as number", {"date": 5}),
        ("date not an instant", {"date": "yesterday"}),
        ("author as object not a list", {"author": {"reference": "Practitioner/1"}}),
        ("author entry as string", {"author": ["Practitioner/1"]}),
        ("authenticator as string", {"authenticator": "Practitioner/1"}),
        ("custodian as string", {"custodian": "Organization/1"}),
        ("masterIdentifier as list", {"masterIdentifier": [{"value": "x"}]}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("relatesTo as object not a list", {"relatesTo": {"code": "replaces"}}),
        (
            "relatesTo code with an unknown value",
            {
                "relatesTo": [
                    {"code": "deletes", "target": {"reference": "DocumentReference/1"}}
                ]
            },
        ),
        (
            "relatesTo target as string",
            {"relatesTo": [{"code": "replaces", "target": "DocumentReference/1"}]},
        ),
        ("description as number", {"description": 5}),
        ("securityLabel as object not a list", {"securityLabel": {"text": "x"}}),
        ("content as object not a list", {"content": {"attachment": {}}}),
        ("content attachment as string", {"content": [{"attachment": "x"}]}),
        (
            "content attachment size as string",
            {"content": [{"attachment": {"size": "big"}}]},
        ),
        ("content format as string", {"content": [{"attachment": {}, "format": "x"}]}),
        ("context as list", {"context": [{"encounter": []}]}),
        (
            "context encounter as object",
            {"context": {"encounter": {"reference": "Encounter/1"}}},
        ),
        ("context period as string", {"context": {"period": "2026"}}),
        (
            "context facilityType as list",
            {"context": {"facilityType": [{"text": "x"}]}},
        ),
        (
            "context related as object",
            {"context": {"related": {"reference": "Condition/1"}}},
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "DocumentReference", "id": "320001", **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.DocumentReference, validate=True
        )
