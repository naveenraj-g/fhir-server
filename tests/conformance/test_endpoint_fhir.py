"""FHIR R4 conformance for `to_fhir_endpoint()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Endpoint is stored Medplum-style (like Organization/Practitioner/
HealthcareService): the resource lives whole in EndpointModel.content, and
to_fhir_endpoint() only stamps `id` and `meta` onto it. So what can go wrong
on the read side is that stamping (e.g. a malformed meta extension) or a
stored document the server returns that isn't valid R4 — each case below is a
`content` document as the write path would store it, run through the real
read mapper. (Unlike most resources, Endpoint has four required elements, so
every case carries them.)
"""

import datetime as dt

import pytest

from app.fhir.mappers.endpoint import to_fhir_endpoint
from app.models.endpoint import EndpointModel
from tests.integration.endpoint.support import FULL, MINIMAL

from .support import assert_valid, fhir_json_text

endpoint_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.endpoint_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)


def _stored(document: dict) -> dict:
    """What the write path stores: everything but resourceType/id/meta."""
    return {
        k: v for k, v in document.items() if k not in ("resourceType", "id", "meta")
    }


def _endpoint(**changes) -> EndpointModel:
    overrides = {
        k: changes.pop(k) for k in ("updated_by", "updated_at") if k in changes
    }
    fields = {
        "endpoint_id": 620001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": {**MINIMAL, **changes},
    }
    fields.update(overrides)
    return EndpointModel(**fields)


CASES = {
    "minimal": _endpoint(),
    "every_status_code": _endpoint(status="entered-in-error"),
    "suspended": _endpoint(status="suspended"),
    "updated_by_and_updated_at": _endpoint(updated_by="u-other", updated_at=D),
    "managing_organization": _endpoint(
        managingOrganization={
            "reference": "Organization/190001",
            "type": "Organization",
            "display": "General Hospital",
            "identifier": {"system": "urn:org-registry", "value": "ORG-9"},
        }
    ),
    "identifier_with_type_and_assigner": _endpoint(
        identifier=[
            {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "EPT",
                        }
                    ]
                },
                "system": "https://fhir-server.dev/fhir/identifier-system/endpoint",
                "value": "EP-1",
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "name_contact_period": _endpoint(
        name="General Hospital FHIR API",
        contact=[
            {"system": "email", "value": "it@example.org", "use": "work", "rank": 1}
        ],
        period={"start": "2026-01-01T00:00:00Z", "end": "2027-01-01T00:00:00Z"},
    ),
    "payload_types_and_mime_types": _endpoint(
        payloadType=[
            {"coding": [{"code": "any", "display": "Any"}], "text": "Any payload"},
            {"text": "Free text only"},
        ],
        payloadMimeType=["application/fhir+json", "application/fhir+xml"],
    ),
    "headers": _endpoint(header=["Authorization: Bearer abc", "X-Tenant: one"]),
    "extension": _endpoint(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full_payload": EndpointModel(
        endpoint_id=620001,
        tenant_id="org-test",
        created_by="u-test",
        created_at=D,
        content=_stored(FULL),
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_endpoint_mapper_emits_valid_fhir_r4(case):
    assert_valid(endpoint_pb2.Endpoint, to_fhir_endpoint(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _stored(FULL)
    out = to_fhir_endpoint(
        EndpointModel(
            endpoint_id=620001,
            tenant_id="org-test",
            created_by="u-test",
            created_at=D,
            content=content,
        )
    )
    assert out["resourceType"] == "Endpoint"
    assert out["id"] == "620001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"nam3": "x"}),
        ("status outside the required binding", {"status": "broken"}),
        ("name as object not string", {"name": {"text": "x"}}),
        ("connectionType as string not Coding", {"connectionType": "hl7-fhir-rest"}),
        ("payloadType as strings not CodeableConcepts", {"payloadType": ["any"]}),
        ("payloadMimeType as objects", {"payloadMimeType": [{"code": "x"}]}),
        (
            "managingOrganization as string not Reference",
            {"managingOrganization": "Organization/1"},
        ),
        ("contact as string not ContactPoint", {"contact": ["it@example.org"]}),
        ("period as string", {"period": "2026"}),
        ("header as objects not strings", {"header": [{"name": "x"}]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Endpoint", "id": "620001", **MINIMAL, **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), endpoint_pb2.Endpoint, validate=True
        )
