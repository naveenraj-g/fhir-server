"""FHIR R4 conformance for `to_fhir_location()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt
from decimal import Decimal

import pytest

from app.fhir.mappers.location import to_fhir_location
from app.models.location import (
    LocationAlias,
    LocationEndpoint,
    LocationHoursOfOperation,
    LocationIdentifier,
    LocationMode,
    LocationModel,
    LocationStatus,
    LocationTelecom,
    LocationType,
)

from .support import assert_valid, fhir_json_text

location_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.location_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


def _location(**overrides) -> LocationModel:
    """A Location carrying only the columns the model marks NOT NULL, plus
    empty sub-resource lists (nothing is lazy-loadable off a session here)."""
    fields = {
        "location_id": 230001,
        "org_id": "org-test",
        "status": LocationStatus.active,
        "name": "South Wing",
        "mode": LocationMode.instance,
        "address_type": "both",
        "address_city": "Den Burg",
        "address_state": "NH",
        "address_postal_code": "9105 PZ",
        "address_country": "NLD",
        "created_by": "u-test",
        "created_at": D,
    }
    fields.update(overrides)
    loc = LocationModel(**fields)
    for attr in (
        "identifiers", "types", "telecoms", "endpoints", "aliases",
        "hours_of_operation",
    ):
        if getattr(loc, attr, None) is None:
            setattr(loc, attr, [])
    return loc


def _with(attr, *rows) -> LocationModel:
    loc = _location()
    setattr(loc, attr, list(rows))
    return loc


def _identifier(**kw) -> LocationIdentifier:
    return LocationIdentifier(
        **{"id": 1, "org_id": "org-test", "system": "http://ex.org/ids",
           "value": "B1-S.F2", "created_by": "u-test", "created_at": D, **kw}
    )


# Each case is one distinct shape the mapper can emit. Anything with a
# conditional branch in app/fhir/mappers/location/fhir.py should appear here.
CASES = {
    "minimal": _location(),

    "status_inactive_mode_kind": _location(
        status=LocationStatus.inactive, mode=LocationMode.kind
    ),
    "status_suspended": _location(status=LocationStatus.suspended),

    "operational_status_full_coding": _location(
        operational_status_system="http://terminology.hl7.org/CodeSystem/v2-0116",
        operational_status_version="2.9",
        operational_status_code="U",
        operational_status_display="Unoccupied",
        operational_status_user_selected=True,
    ),
    "physical_type_with_text": _location(
        physical_type_system="http://terminology.hl7.org/CodeSystem/location-physical-type",
        physical_type_code="ro",
        physical_type_display="Room",
        physical_type_text="A room",
        physical_type_user_selected=False,
    ),

    "address_full": _location(
        address_use="work",
        address_text="Galapagosweg 91, Building A",
        address_line="Galapagosweg 91, Building A",
        address_district="Texel",
        address_period_start=D,
        address_period_end=D,
    ),

    "position_lon_lat": _location(
        position_longitude=Decimal("-83.69456930"),
        position_latitude=Decimal("42.25475478"),
    ),
    "position_with_altitude": _location(
        position_longitude=Decimal("-83.69456930"),
        position_latitude=Decimal("42.25475478"),
        position_altitude=Decimal("123.45000000"),
    ),

    "managing_organization_resolved": _location(
        managing_organization_type="Organization",
        managing_organization_id=190001,
        managing_organization_display="Burgers UMC",
    ),
    "managing_organization_identifier_fallback": _location(
        managing_organization_identifier_system="urn:org-registry",
        managing_organization_identifier_value="ORG-9",
        managing_organization_identifier_use="official",
    ),
    "part_of_resolved": _location(
        part_of_type="Location", part_of_id=230000, part_of_display="Main Building"
    ),
    "part_of_identifier_fallback": _location(
        part_of_identifier_system="urn:loc-registry",
        part_of_identifier_value="LOC-9",
    ),

    "identifier_with_type_and_period": _with(
        "identifiers",
        _identifier(
            use="official",
            type_system="http://terminology.hl7.org/CodeSystem/v2-0203",
            type_version="2.9",
            type_code="PRN",
            type_display="Provider number",
            type_text="Provider number",
            type_user_selected=True,
            period_start=D,
            period_end=D,
        ),
    ),
    "identifier_assigner_resolved": _with(
        "identifiers",
        _identifier(
            assigner_type="Organization", assigner_id=190001, assigner_display="Acme"
        ),
    ),
    "identifier_assigner_fallback": _with(
        "identifiers",
        _identifier(
            assigner_identifier_system="urn:external-registry",
            assigner_identifier_value="EXTERNAL-1",
            assigner_identifier_use="official",
        ),
    ),

    "type_with_text": _with(
        "types",
        LocationType(
            id=1, org_id="org-test",
            coding_system="http://terminology.hl7.org/CodeSystem/v3-RoleCode",
            coding_version="2.0", coding_code="HOSP", coding_display="Hospital",
            text="Hospital", coding_user_selected=True,
            created_by="u-test", created_at=D,
        ),
    ),
    "aliases": _with(
        "aliases",
        *[
            LocationAlias(id=i, org_id="org-test", value=v, created_by="u-test", created_at=D)
            for i, v in enumerate(["South Wing OR", "SW"], 1)
        ],
    ),
    "telecoms_with_rank_and_period": _with(
        "telecoms",
        LocationTelecom(
            id=1, org_id="org-test", system="phone", value="2328", use="work",
            rank=1, period_start=D, period_end=D, created_by="u-test", created_at=D,
        ),
        LocationTelecom(
            id=2, org_id="org-test", system="email", value="a@b.example",
            created_by="u-test", created_at=D,
        ),
    ),

    "hours_all_day_no_times": _with(
        "hours_of_operation",
        LocationHoursOfOperation(
            id=1, org_id="org-test", days_of_week="sat,sun", all_day=True,
            created_by="u-test", created_at=D,
        ),
    ),
    "hours_all_seven_days_edge_times": _with(
        "hours_of_operation",
        LocationHoursOfOperation(
            id=1, org_id="org-test", days_of_week="mon,tue,wed,thu,fri,sat,sun",
            all_day=False, opening_time=dt.time(0, 0),
            closing_time=dt.time(23, 59, 59), created_by="u-test", created_at=D,
        ),
    ),

    "endpoint_resolved": _with(
        "endpoints",
        LocationEndpoint(
            id=1, org_id="org-test", reference_type="Endpoint", reference_id=7,
            reference_display="Main endpoint", created_by="u-test", created_at=D,
        ),
    ),
    "endpoint_identifier_fallback": _with(
        "endpoints",
        LocationEndpoint(
            id=1, org_id="org-test", reference_identifier_system="urn:ext-endpoint",
            reference_identifier_value="EP-1", created_by="u-test", created_at=D,
        ),
    ),

    "availability_exceptions": _location(
        availability_exceptions="Reduced services on public holidays"
    ),
    "description": _location(description="Second floor of the Old South Wing"),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_location_mapper_emits_valid_fhir_r4(case):
    assert_valid(location_pb2.Location, to_fhir_location(CASES[case]))


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.

@pytest.mark.parametrize(
    "label,broken",
    [
        ("bad status code", {"status": "bogus"}),
        ("bad mode code", {"mode": "sideways"}),
        ("misspelled element", {"availabilityException": "x"}),
        ("operationalStatus as CodeableConcept", {"operationalStatus": {"coding": [{"code": "U"}]}}),
        ("alias as objects not strings", {"alias": [{"value": "SW"}]}),
        ("bad daysOfWeek code", {"hoursOfOperation": [{"daysOfWeek": ["funday"]}]}),
        ("openingTime not a time", {"hoursOfOperation": [{"openingTime": "9am"}]}),
        ("position missing latitude", {"position": {"longitude": -83.6}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Location", "id": "230001", "status": "active",
        "name": "South Wing", **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), location_pb2.Location, validate=True
        )
