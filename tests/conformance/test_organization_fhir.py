"""FHIR R4 conformance for `to_fhir_organization()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Organization is stored Medplum-style: the resource lives whole in
OrganizationModel.content, and to_fhir_organization() only stamps `id` and
`meta` onto it. So what can go wrong on the read side is that stamping
(e.g. a malformed meta extension) or a stored document the server returns
that isn't valid R4 — each case below is a `content` document as the write
path would store it, run through the real read mapper.
"""

import datetime as dt
import json
from pathlib import Path

import pytest

from app.fhir.mappers.organization import to_fhir_organization
from app.models.organization import OrganizationModel

from .support import assert_valid, fhir_json_text

organization_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.organization_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

_FIXTURE = (
    Path(__file__).parents[1]
    / "integration" / "organization" / "fixtures" / "r4_full_organization.json"
)


def _org(content: dict, **overrides) -> OrganizationModel:
    fields = {
        "organization_id": 190001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return OrganizationModel(**fields)


def _stored(document: dict) -> dict:
    """What the write path stores: everything but resourceType/id/meta."""
    return {k: v for k, v in document.items() if k not in ("resourceType", "id", "meta")}


CASES = {
    "minimal": _org({"name": "Acme Health"}),
    "active_false": _org({"active": False, "name": "Acme Health"}),
    "updated_by_and_updated_at": _org(
        {"name": "Acme Health"}, updated_by="u-other", updated_at=D
    ),
    "partof_with_type_and_identifier": _org({
        "name": "Acme Clinic",
        "partOf": {
            "reference": "Organization/190000",
            "type": "Organization",
            "display": "Acme Group",
            "identifier": {"system": "urn:org-registry", "value": "ORG-9"},
        },
    }),
    "extension": _org({
        "name": "Acme Health",
        "extension": [{"url": "https://fhir-server.dev/fhir/StructureDefinition/x", "valueString": "y"}],
    }),
    "full_r4_payload": _org(_stored(json.loads(_FIXTURE.read_text()))),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_organization_mapper_emits_valid_fhir_r4(case):
    assert_valid(organization_pb2.Organization, to_fhir_organization(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _stored(json.loads(_FIXTURE.read_text()))
    out = to_fhir_organization(_org(content))
    assert out["resourceType"] == "Organization"
    assert out["id"] == "190001"
    assert {k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")} == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.

@pytest.mark.parametrize(
    "label,broken",
    [
        ("active as string not boolean", {"active": "yes"}),
        ("misspelled element", {"nam3": "Acme Health"}),
        ("identifier as string not object", {"identifier": ["ORG-1"]}),
        ("type as strings not CodeableConcepts", {"type": ["prov"]}),
        ("alias as objects not strings", {"alias": [{"value": "Acme"}]}),
        ("partOf as string not Reference", {"partOf": "Organization/190000"}),
        ("contact.address as string not Address", {"contact": [{"address": "somewhere"}]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Organization", "id": "190001", "active": True,
        "name": "Acme Health", **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), organization_pb2.Organization, validate=True
        )
