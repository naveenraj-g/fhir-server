"""FHIR R4 conformance for `to_fhir_location()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Location is stored Medplum-style, like Organization: the resource lives
whole in LocationModel.content, and to_fhir_location() only stamps `id`
and `meta` onto it. Each case below is a `content` document as the write
path would store it, run through the real read mapper.
"""

import datetime as dt
import json
from pathlib import Path

import pytest

from app.fhir.mappers.location import to_fhir_location
from app.models.location import LocationModel

from .support import assert_valid, fhir_json_text

location_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.location_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

_FIXTURE = Path(__file__).parents[1] / "integration" / "location" / "fixtures" / "r4_full_location.json"


def _loc(content: dict, **overrides) -> LocationModel:
    fields = {
        "location_id": 230001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return LocationModel(**fields)


def _stored(document: dict) -> dict:
    """What the write path stores: everything but resourceType/id/meta."""
    return {k: v for k, v in document.items() if k not in ("resourceType", "id", "meta")}


CASES = {
    "minimal": _loc({"name": "Main Building"}),
    "empty": _loc({}),
    "updated_by_and_updated_at": _loc({"name": "Main Building"}, updated_by="u-other", updated_at=D),
    "kind_mode": _loc({"mode": "kind", "type": [{"coding": [{"code": "AMB"}]}]}),
    "references_with_identifier": _loc({
        "managingOrganization": {"reference": "Organization/190001", "display": "Acme"},
        "partOf": {"identifier": {"system": "urn:reg", "value": "R-1"}},
    }),
    "full_r4_payload": _loc(_stored(json.loads(_FIXTURE.read_text()))),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_location_mapper_emits_valid_fhir_r4(case):
    assert_valid(location_pb2.Location, to_fhir_location(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _stored(json.loads(_FIXTURE.read_text()))
    out = to_fhir_location(_loc(content))
    assert out["resourceType"] == "Location"
    assert out["id"] == "230001"
    assert {k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")} == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating, every test above would keep passing
# while checking nothing. These deliberately-broken payloads prove it still bites.

@pytest.mark.parametrize(
    "label,broken",
    [
        ("status outside required binding", {"status": "open"}),
        ("mode outside required binding", {"mode": "both"}),
        ("misspelled element", {"nam3": "Main Building"}),
        # Not "address as a list": the oracle accepts a one-element array
        # where R4 says 0..1 (documented in CLAUDE.md); base R4 validation
        # rejects it on write — see tests/integration/location/test_core.py.
        ("position latitude as string", {"position": {"longitude": 1, "latitude": "north"}}),
        ("daysOfWeek outside required binding", {"hoursOfOperation": [{"daysOfWeek": ["monday"]}]}),
        ("partOf as string not Reference", {"partOf": "Location/230000"}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Location", "id": "230001", "name": "Main Building", **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), location_pb2.Location, validate=True
        )
