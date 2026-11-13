"""
FHIR R4 Location search parameters
(https://www.hl7.org/fhir/R4/location.html#search) plus the common
`_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL,
`_sort`, `_include`/`_revinclude`, and the OpenAPI docs all come from
location_search() below. Same arrangement as
app.repository.organization.search.

Each parameter's SQL reads only the search index (LocationModel's columns
and child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

import itertools
import math
from functools import cache

from sqlalchemy import Float, cast, exists, false, func, literal, or_, select, true
from sqlalchemy.orm import aliased

from app.fhir.search import IncludeTarget, MultiValueSort, SearchError, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    ArrayAggregate,
    array_string_match,
    coded_token_match,
    date_match,
    earliest,
    reference_match,
    reference_target,
    string_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import parse_of_type, parse_token, split_escaped, unescape
from app.models.enums import OrganizationReferenceType
from app.models.location import (
    LocationEndpoint,
    LocationIdentifier,
    LocationModel,
    LocationPartOfReferenceType,
    LocationStatus,
    LocationType,
)
from app.models.location.enums import LocationEndpointReferenceType
from app.schemas.enums import AddressUse

Loc = LocationModel
_ADDRESS_USE_SYSTEM = "http://hl7.org/fhir/address-use"
_STATUS_SYSTEM = "http://hl7.org/fhir/location-status"
_cte_names = itertools.count(1)


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(select(literal(1)).where(model.location_pk == Loc.id, *conditions))


def _child_sort(column, model):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return select(fn(column)).where(model.location_pk == Loc.id).scalar_subquery()

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def _name_sort():
    """_sort key for `name`, whose expression is `name | alias`: the name or
    any alias, whichever comes first in the requested order."""
    return MultiValueSort(
        ascending=earliest(Loc.name_norm, ArrayAggregate(Loc.alias_norm, "min"), descending=False),
        descending=earliest(Loc.name_norm, ArrayAggregate(Loc.alias_norm, "max"), descending=True),
    )


def last_updated():
    return func.coalesce(Loc.updated_at, Loc.created_at)


# ── _id ──────────────────────────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system or not (token.code or "").isdigit():  # ids are the numeric public id
        return false()
    return Loc.location_id == int(token.code)


# ── tokens with a fixed code system: status, address-use ─────────────────────


def _fixed_system_token(column, system, enum_cls):
    """A `code`-typed element bound to one code system (status,
    address.use): `code` or `system|code`; another system or `|code` (no
    system) never matches; an unknown code matches nothing (rather than
    failing the Postgres enum cast)."""

    def match(value, modifier, ctx):
        token = parse_token(value)
        if token.system is not None and token.system != system:
            return false()
        if token.code is None:
            return column.is_not(None)
        try:
            return column == enum_cls(token.code)
        except ValueError:
            return false()

    return match


# ── strings ──────────────────────────────────────────────────────────────────


def _name_match(value, modifier, ctx):
    return or_(
        string_match(Loc.name, Loc.name_norm, value, modifier),
        array_string_match(Loc.alias, Loc.alias_norm, value, modifier),
    )


_ADDRESS_PARTS = {
    "text": (Loc.address_text, Loc.address_text_norm),
    "city": (Loc.address_city, Loc.address_city_norm),
    "district": (Loc.address_district, Loc.address_district_norm),
    "state": (Loc.address_state, Loc.address_state_norm),
    "postal_code": (Loc.address_postal_code, Loc.address_postal_code_norm),
    "country": (Loc.address_country, Loc.address_country_norm),
}


def _address_match(value, modifier, ctx):
    # R4: matches any of the string fields in the Address — each line on
    # its own, city, district, state, country, postalCode, text.
    return or_(
        array_string_match(Loc.address_line, Loc.address_line_norm, value, modifier),
        *(string_match(raw, norm, value, modifier) for raw, norm in _ADDRESS_PARTS.values()),
    )


def _address_present(ctx):
    return or_(
        Loc.address_line.is_not(None),
        Loc.address_use.is_not(None),
        *(raw.is_not(None) for raw, _ in _ADDRESS_PARTS.values()),
    )


def _address_part(part):
    raw, norm = _ADDRESS_PARTS[part]
    return (lambda value, modifier, ctx: string_match(raw, norm, value, modifier)), (
        lambda ctx: raw.is_not(None)
    )


# ── identifier / type / operational-status ───────────────────────────────────

_I = LocationIdentifier
_T = LocationType


def _identifier_match(value, modifier, ctx):
    if modifier == "text":
        return _exists(_I, token_text_match((_I.type_text_norm, _I.type_display_norm), value))
    if modifier == "of-type":
        type_system, type_code, ident = parse_of_type(value)
        return _exists(_I, _I.type_system == type_system, _I.type_code == type_code, _I.value == ident)
    return _exists(_I, token_match(_I.system, _I.value, value))


def _type_match(value, modifier, ctx):
    return _exists(_T, coded_token_match(_T.system, _T.code, value, modifier, (_T.text_norm, _T.display_norm)))


def _operational_status_match(value, modifier, ctx):
    # operationalStatus is a single Coding: `:text` searches its display.
    return coded_token_match(
        Loc.operational_status_system,
        Loc.operational_status_code,
        value,
        modifier,
        (Loc.operational_status_display_norm,),
    )


# ── references ───────────────────────────────────────────────────────────────


def _organization_match(value, modifier, ctx):
    if modifier == "identifier":
        return token_condition(
            Loc.managing_organization_identifier_system,
            Loc.managing_organization_identifier_value,
            parse_token(value),
        )
    return reference_match(
        Loc.managing_organization_type, Loc.managing_organization_id, Loc.managing_organization_reference,
        value, modifier, ctx, ("Organization",), OrganizationReferenceType,
    )


def _organization_present(ctx):
    return or_(
        Loc.managing_organization_reference.is_not(None),
        Loc.managing_organization_identifier_value.is_not(None),
    )


def _organization_chain(target, inner, ctx):
    """`organization.<param>=v`: managingOrganization is an Organization
    (same tenant) matching any Organization search parameter."""
    from app.models.organization import OrganizationModel as Org

    referenced = select(Org.organization_id).where(Org.tenant_id == ctx.tenant_id, inner).correlate(None)
    return Loc.managing_organization_id.in_(referenced)


def _partof_match(value, modifier, ctx):
    if modifier == "identifier":
        return token_condition(Loc.part_of_identifier_system, Loc.part_of_identifier_value, parse_token(value))
    return reference_match(
        Loc.part_of_type, Loc.part_of_id, Loc.part_of_reference, value, modifier, ctx,
        ("Location",), LocationPartOfReferenceType,
    )


def _partof_present(ctx):
    return or_(Loc.part_of_reference.is_not(None), Loc.part_of_identifier_value.is_not(None))


def _partof_chain(target, inner, ctx):
    """`partof.<param>=v`: partOf is a Location (same tenant) matching
    `<param>=v`. Doesn't correlate to the outer row — it ranges over the
    referenced Location."""
    referenced = select(Loc.location_id).where(Loc.tenant_id == ctx.tenant_id, inner).correlate(None)
    return Loc.part_of_id.in_(referenced)


def _partof_hierarchy(value, direction, ctx, max_depth: int = 100):
    """`partof:below=X` — locations anywhere inside X (partOf is X, or a
    location inside X). `partof:above=X` — locations whose partOf is X or
    one of X's ancestors. Recursive CTE, scoped to the caller's tenant."""
    ref = reference_target(value, None, ("Location",), ctx.fhir_base)
    if ref is None or ref.url is not None:
        return false()
    x = int(ref.resource_id)
    seed, step = aliased(Loc), aliased(Loc)
    name = f"location_partof_{direction}_{next(_cte_names)}"
    if direction == "below":
        tree = (
            select(seed.location_id.label("lid"), literal(1).label("depth"))
            .where(seed.part_of_id == x, seed.tenant_id == ctx.tenant_id)
            .cte(name=name, recursive=True)
        )
        tree = tree.union_all(
            select(step.location_id, tree.c.depth + 1).where(
                step.part_of_id == tree.c.lid, step.tenant_id == ctx.tenant_id, tree.c.depth < max_depth
            )
        )
        return Loc.location_id.in_(select(tree.c.lid))
    tree = (
        select(seed.location_id.label("lid"), seed.part_of_id.label("pid"), literal(1).label("depth"))
        .where(seed.location_id == x, seed.tenant_id == ctx.tenant_id)
        .cte(name=name, recursive=True)
    )
    tree = tree.union_all(
        select(step.location_id, step.part_of_id, tree.c.depth + 1).where(
            step.location_id == tree.c.pid, step.tenant_id == ctx.tenant_id, tree.c.depth < max_depth
        )
    )
    return or_(Loc.part_of_id == x, Loc.part_of_id.in_(select(tree.c.lid)))


_E = LocationEndpoint


def _endpoint_match(value, modifier, ctx):
    if modifier == "identifier":
        return _exists(
            _E, token_condition(_E.reference_identifier_system, _E.reference_identifier_value, parse_token(value))
        )
    return _exists(
        _E,
        reference_match(
            _E.reference_type, _E.reference_id, _E.reference_reference, value, modifier, ctx,
            ("Endpoint",), LocationEndpointReferenceType,
        ),
    )


# ── near (special) ───────────────────────────────────────────────────────────
# near=[latitude]|[longitude]|[distance]|[units], WGS84
# (https://www.hl7.org/fhir/R4/location.html#positional).

# Distance units, UCUM codes (plus the plain spellings clients send).
_UNITS_IN_KM = {
    "km": 1.0,
    "m": 0.001,
    "mi": 1.609344,
    "[mi_i]": 1.609344,
    "[mi_us]": 1.609347,
    "ft": 0.0003048,
    "[ft_i]": 0.0003048,
}
# R4: "If the units are omitted, then kms should be assumed. If the distance
# is omitted, then the server can use its own discretion as to what
# distances should be considered near (and units are irrelevant)."
DEFAULT_NEAR_KM = 50.0
_EARTH_RADIUS_KM = 6371.0088
LOCATION_DISTANCE_URL = "http://hl7.org/fhir/StructureDefinition/location-distance"


def parse_near(value: str) -> tuple[float, float, float, str]:
    """(latitude, longitude, distance_km, unit as given) — 400 when malformed."""
    parts = [unescape(p) for p in split_escaped(value, "|")]
    if len(parts) < 2 or len(parts) > 4:
        raise SearchError(value, f"Invalid near '{value}': expected latitude|longitude[|distance[|units]].")
    try:
        lat, lon = float(parts[0]), float(parts[1])
        distance = float(parts[2]) if len(parts) > 2 and parts[2] != "" else None
    except ValueError:
        raise SearchError(value, f"Invalid near '{value}': latitude, longitude and distance must be numbers.") from None
    unit = (parts[3] if len(parts) > 3 else "") or "km"
    if unit not in _UNITS_IN_KM:
        raise SearchError(value, f"Invalid near units '{unit}': expected one of {', '.join(_UNITS_IN_KM)}.")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise SearchError(value, "Invalid near: latitude must be within [-90, 90], longitude within [-180, 180].")
    if distance is not None and distance < 0:
        raise SearchError(value, "Invalid near: distance must not be negative.")
    km = DEFAULT_NEAR_KM if distance is None else distance * _UNITS_IN_KM[unit]
    return lat, lon, km, unit if distance is not None else "km"


def _great_circle_km(lat: float, lon: float):
    """SQL: great-circle distance (spherical law of cosines) from the point
    to each row's position, in km. Plain trig functions — no PostGIS — and
    registered on the SQLite test DB in tests/conftest.py. The clamp keeps
    acos() inside its domain against rounding."""
    lat_rad, lon_rad = math.radians(lat), math.radians(lon)
    row_lat = func.radians(cast(Loc.position_latitude, Float))
    row_lon = func.radians(cast(Loc.position_longitude, Float))
    cosine = func.sin(lat_rad) * func.sin(row_lat) + func.cos(lat_rad) * func.cos(row_lat) * func.cos(
        row_lon - lon_rad
    )
    return _EARTH_RADIUS_KM * func.acos(func.least(1.0, func.greatest(-1.0, cosine)))


def _near_match(value, modifier, ctx):
    lat, lon, km, _ = parse_near(value)
    return (Loc.position_latitude.is_not(None)) & (_great_circle_km(lat, lon) <= km)


def _distance_km(lat1, lon1, lat2, lon2) -> float:
    """The same distance in Python, for the result's location-distance extension."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    cosine = math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(math.radians(lon2 - lon1))
    return _EARTH_RADIUS_KM * math.acos(max(-1.0, min(1.0, cosine)))


def near_distance_extensions(request, loc) -> list[dict] | None:
    """R4: each `near` match carries its distance in the entry's search
    element — `location-distance` (valueDistance). With several points
    (comma OR, or repeated), the distance to the closest is reported, in the
    first point's units."""
    points = [
        parse_near(v) for c in request.clauses if c.name == "near" and c.chain is None for v in c.values
    ]
    if not points or loc.position_latitude is None:
        return None
    lat, lon = float(loc.position_latitude), float(loc.position_longitude)
    km = min(_distance_km(p[0], p[1], lat, lon) for p in points)
    unit = points[0][3]
    value = round(km / _UNITS_IN_KM[unit], 3)
    code = {"mi": "[mi_i]", "ft": "[ft_i]"}.get(unit, unit)
    return [
        {
            "url": LOCATION_DISTANCE_URL,
            "valueDistance": {"value": value, "unit": unit, "system": "http://unitsofmeasure.org", "code": code},
        }
    ]


# ── _include / _revinclude ───────────────────────────────────────────────────


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


async def _include_organization(session, ctx, locations):
    """_include=Location:organization — the managing organizations."""
    from app.models.organization import OrganizationModel as Org

    ids = {loc.managing_organization_id for loc in locations if loc.managing_organization_id is not None}
    if not ids:
        return []
    return await _fetch(session, select(Org).where(Org.tenant_id == ctx.tenant_id, Org.organization_id.in_(ids)))


async def _include_partof(session, ctx, locations):
    """_include=Location:partof — the containing locations."""
    ids = {loc.part_of_id for loc in locations if loc.part_of_id is not None}
    if not ids:
        return []
    return await _fetch(session, select(Loc).where(Loc.tenant_id == ctx.tenant_id, Loc.location_id.in_(ids)))


async def _revinclude_partof(session, ctx, locations):
    """_revinclude=Location:partof — the locations inside these ones."""
    ids = {loc.location_id for loc in locations}
    return await _fetch(session, select(Loc).where(Loc.tenant_id == ctx.tenant_id, Loc.part_of_id.in_(ids)))


def _register_kind() -> None:
    """How the search engine identifies and renders Location rows — for
    Location searches and for Locations included by others."""
    from app.fhir.mappers.location import to_fhir_location
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(ResourceKind("Location", lambda loc: loc.location_id, to_fhir_location, "locations"))


# ── registry ─────────────────────────────────────────────────────────────────

_city, _city_present = _address_part("city")
_state, _state_present = _address_part("state")
_country, _country_present = _address_part("country")
_postal, _postal_present = _address_part("postal_code")

_STRING = frozenset({"exact", "contains", "missing"})
_CODED = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})


@cache
def location_search() -> SearchRegistry:
    from app.repository.organization.search import organization_search

    _register_kind()
    organization_search()  # make sure Organization's kind is registered for includes
    params = [
        SearchParam(
            "_id", "token", "Logical id of the resource (the public location id)", "Resource.id",
            _id_match, lambda ctx: true(), frozenset({"not", "missing"}),
            sort=lambda: Loc.location_id, example="230001",
        ),
        SearchParam(
            "_lastUpdated", "date", "When the resource last changed (meta.lastUpdated)", "Resource.meta.lastUpdated",
            lambda v, m, ctx: date_match(last_updated(), v), lambda ctx: true(),
            sort=last_updated, example="ge2024-01-01",
        ),
        SearchParam(
            "address", "string",
            "A (part of the) address of the location — any of line, city, district, state, country, "
            "postalCode, text",
            "Location.address", _address_match, _address_present, _STRING, example="Main St",
        ),
        SearchParam(
            "address-city", "string", "A city specified in an address", "Location.address.city",
            _city, _city_present, _STRING, sort=lambda: Loc.address_city_norm, example="Springfield",
        ),
        SearchParam(
            "address-country", "string", "A country specified in an address", "Location.address.country",
            _country, _country_present, _STRING, sort=lambda: Loc.address_country_norm, example="US",
        ),
        SearchParam(
            "address-postalcode", "string", "A postal code specified in an address",
            "Location.address.postalCode", _postal, _postal_present, _STRING,
            sort=lambda: Loc.address_postal_code_norm, example="62701",
        ),
        SearchParam(
            "address-state", "string", "A state specified in an address", "Location.address.state",
            _state, _state_present, _STRING, sort=lambda: Loc.address_state_norm, example="IL",
        ),
        SearchParam(
            "address-use", "token",
            f"A use code specified in an address (home | work | temp | old | billing; system {_ADDRESS_USE_SYSTEM})",
            "Location.address.use", _fixed_system_token(Loc.address_use, _ADDRESS_USE_SYSTEM, AddressUse),
            lambda ctx: Loc.address_use.is_not(None), frozenset({"not", "missing"}),
            sort=lambda: Loc.address_use, example="work",
        ),
        SearchParam(
            "endpoint", "reference", "Technical endpoints providing access to services operated for the location",
            "Location.endpoint", _endpoint_match, lambda ctx: _exists(_E), frozenset({"identifier", "missing"}),
            targets=("Endpoint",), example="Endpoint/1",
        ),
        SearchParam(
            "identifier", "token", "An identifier for the location", "Location.identifier",
            _identifier_match, lambda ctx: _exists(_I), frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="https://fhir-server.dev/fhir/identifier-system/location-ids|B1-S.F2",
            modifier_docs={"text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."},
        ),
        SearchParam(
            "name", "string", "A portion of the location's name or alias", "Location.name | Location.alias",
            _name_match, lambda ctx: or_(Loc.name.is_not(None), Loc.alias.is_not(None)), _STRING,
            sort=_name_sort, example="South Wing",
        ),
        SearchParam(
            "near", "special",
            "Search for locations where the location.position is near to, or within a specified distance of, "
            "the provided coordinates (WGS84): `latitude|longitude|distance|units`, e.g. "
            "`42.256500|-83.694810|11.20|km`. Units: km (default), m, [mi_i] / mi, [ft_i] / ft; without a "
            f"distance, {DEFAULT_NEAR_KM:g} km. Each match reports its distance in the entry's `search` element "
            f"({LOCATION_DISTANCE_URL}). Comma-separated points are OR'd.",
            "Location.position", _near_match, lambda ctx: Loc.position_latitude.is_not(None), frozenset(),
            example="42.256500|-83.694810|11.20|km",
        ),
        SearchParam(
            "operational-status", "token",
            "Searches for locations (typically bed/room) that have an operational status (e.g. contaminated, "
            "housekeeping)",
            "Location.operationalStatus", _operational_status_match,
            lambda ctx: or_(Loc.operational_status_code.is_not(None), Loc.operational_status_system.is_not(None)),
            _CODED, sort=lambda: Loc.operational_status_code,
            example="http://terminology.hl7.org/CodeSystem/v2-0116|U",
            modifier_docs={"text": "`:text` — string search (starts-with) on the operationalStatus Coding's display."},
        ),
        SearchParam(
            "organization", "reference", "Searches for locations that are managed by the provided organization",
            "Location.managingOrganization", _organization_match, _organization_present,
            frozenset({"identifier", "missing"}), targets=("Organization",), chain=_organization_chain,
            chain_targets={"Organization": organization_search}, sort=lambda: Loc.managing_organization_id,
            example="Organization/190001",
        ),
        SearchParam(
            "partof", "reference", "A location of which this location is a part", "Location.partOf",
            _partof_match, _partof_present, frozenset({"identifier", "above", "below", "missing"}),
            targets=("Location",), chain=_partof_chain, chain_targets={"Location": location_search},
            hierarchy=_partof_hierarchy, sort=lambda: Loc.part_of_id, example="Location/230001",
            modifier_docs={
                "below": "`:below` — locations anywhere inside the given one (rooms in a wing in a building, ...).",
                "above": "`:above` — locations whose partOf is the given one or any location containing it.",
            },
        ),
        SearchParam(
            "status", "token", f"Searches for locations with a specific kind of status (active | suspended | "
            f"inactive; system {_STATUS_SYSTEM})",
            "Location.status", _fixed_system_token(Loc.status, _STATUS_SYSTEM, LocationStatus),
            lambda ctx: Loc.status.is_not(None), frozenset({"not", "missing"}),
            sort=lambda: Loc.status, example="active",
        ),
        SearchParam(
            "type", "token", "A code for the type of location", "Location.type",
            _type_match, lambda ctx: _exists(_T), _CODED, sort=lambda: _child_sort(_T.code, _T),
            example="http://terminology.hl7.org/CodeSystem/v3-RoleCode|HOSP",
        ),
    ]
    return SearchRegistry(
        resource_type="Location",
        params={p.name: p for p in params},
        summary_elements=frozenset(
            {"identifier", "status", "operationalStatus", "name", "description", "mode", "type",
             "physicalType", "managingOrganization"}
        ),
        includes=(
            IncludeTarget("Location", "organization", "Organization", _include_organization),
            IncludeTarget("Location", "partof", "Location", _include_partof),
            # Endpoint isn't a resource on this server: accepted, adds nothing.
            IncludeTarget("Location", "endpoint", "Endpoint"),
        ),
        revincludes=(IncludeTarget("Location", "partof", "Location", _revinclude_partof, reverse=True),),
        default_sort=lambda: [Loc.location_id.desc()],
        entry_extensions=near_distance_extensions,
    )
