"""
FHIR R4 Organization search parameters
(https://www.hl7.org/fhir/R4/organization.html#search) plus the common
`_id` / `_lastUpdated`, declared once for app.fhir.search: parsing,
SQL, `_sort`, `_include`, and the OpenAPI docs all come from
ORGANIZATION_SEARCH below.

Each parameter's SQL reads only the search index (OrganizationModel's
columns and child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

import itertools
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true
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
from app.fhir.search.values import parse_of_type, parse_token
from app.models.enums import OrganizationReferenceType
from app.models.organization import (
    OrganizationAddress,
    OrganizationEndpoint,
    OrganizationIdentifier,
    OrganizationModel,
    OrganizationType,
)
from app.models.organization.enums import OrganizationEndpointReferenceType
from app.schemas.enums import AddressUse

Org = OrganizationModel
_ADDRESS_USE_SYSTEM = "http://hl7.org/fhir/address-use"
_cte_names = itertools.count(1)


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(select(literal(1)).where(model.organization_pk == Org.id, *conditions))


def _child_sort(column, model):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return select(fn(column)).where(model.organization_pk == Org.id).scalar_subquery()

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def _name_sort():
    """_sort key for `name`, whose expression is `name | alias`: the name or
    any alias, whichever comes first in the requested order."""
    return MultiValueSort(
        ascending=earliest(Org.name_norm, ArrayAggregate(Org.alias_norm, "min"), descending=False),
        descending=earliest(Org.name_norm, ArrayAggregate(Org.alias_norm, "max"), descending=True),
    )


def last_updated():
    return func.coalesce(Org.updated_at, Org.created_at)


# ── _id / _lastUpdated ───────────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system or not (token.code or "").isdigit():  # ids are the numeric public id
        return false()
    return Org.organization_id == int(token.code)


# ── active / address-use (tokens with a fixed code system) ───────────────────


def _active_match(value, modifier, ctx):
    token = parse_token(value)
    if token.code not in ("true", "false") or token.system:  # boolean: no code system
        raise SearchError(value, f"'active' takes true or false, not '{value}'.")
    return Org.active.is_(token.code == "true")


def _address_use_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system is not None and token.system != _ADDRESS_USE_SYSTEM:
        return false()  # another system, or `|code` (no system) — address-use is always coded in its own
    if token.code is None:
        return _exists(OrganizationAddress, OrganizationAddress.use.is_not(None))
    try:
        use = AddressUse(token.code)
    except ValueError:
        return false()
    return _exists(OrganizationAddress, OrganizationAddress.use == use)


# ── strings ──────────────────────────────────────────────────────────────────


def _name_match(value, modifier, ctx):
    return or_(
        string_match(Org.name, Org.name_norm, value, modifier),
        array_string_match(Org.alias, Org.alias_norm, value, modifier),
    )


def _phonetic_match(value, modifier, ctx):
    from app.core.phonetic import phonetic_codes

    codes = phonetic_codes(value)
    if not codes:
        return false()
    # Every word of the query must sound like some word of the name.
    return and_(*(Org.name_phonetic.like(f"% {code} %") for code in codes))


_A = OrganizationAddress
_ADDRESS_PARTS = {
    "text": (_A.text, _A.text_norm),
    "city": (_A.city, _A.city_norm),
    "district": (_A.district, _A.district_norm),
    "state": (_A.state, _A.state_norm),
    "postal_code": (_A.postal_code, _A.postal_code_norm),
    "country": (_A.country, _A.country_norm),
}


def _address_match(value, modifier, ctx):
    # R4: "may match any of the string fields in the Address, including
    # line, city, district, state, country, postalCode, and/or text".
    return _exists(
        _A,
        or_(
            array_string_match(_A.line, _A.line_norm, value, modifier),
            *(string_match(raw, norm, value, modifier) for raw, norm in _ADDRESS_PARTS.values()),
        ),
    )


def _address_part(part):
    raw, norm = _ADDRESS_PARTS[part]

    def match(value, modifier, ctx):
        return _exists(_A, string_match(raw, norm, value, modifier))

    def present(ctx):
        return _exists(_A, raw.is_not(None))

    return match, present


# ── identifier / type ────────────────────────────────────────────────────────

_I = OrganizationIdentifier
_T = OrganizationType


def _identifier_match(value, modifier, ctx):
    if modifier == "text":
        return _exists(_I, token_text_match((_I.type_text_norm, _I.type_display_norm), value))
    if modifier == "of-type":
        type_system, type_code, ident = parse_of_type(value)
        return _exists(_I, _I.type_system == type_system, _I.type_code == type_code, _I.value == ident)
    return _exists(_I, token_match(_I.system, _I.value, value))


def _type_match(value, modifier, ctx):
    return _exists(_T, coded_token_match(_T.system, _T.code, value, modifier, (_T.text_norm, _T.display_norm)))


# ── references ───────────────────────────────────────────────────────────────


def _partof_match(value, modifier, ctx):
    if modifier == "identifier":
        return token_condition(Org.partof_identifier_system, Org.partof_identifier_value, parse_token(value))
    return reference_match(
        Org.partof_type, Org.partof_id, Org.partof_reference, value, modifier, ctx,
        ("Organization",), OrganizationReferenceType,
    )


def _partof_present(ctx):
    return or_(Org.partof_reference.is_not(None), Org.partof_identifier_value.is_not(None))


def _partof_hierarchy(value, direction, ctx, max_depth: int = 100):
    """`partof:below=X` — organizations anywhere below X in the partOf
    hierarchy (partOf is X, or an organization below X). `partof:above=X` —
    organizations whose partOf is X or one of X's ancestors. Walked with a
    recursive CTE, scoped to the caller's tenant."""
    ref = reference_target(value, None, ("Organization",), ctx.fhir_base)
    if ref is None or ref.url is not None:
        return false()
    x = int(ref.resource_id)
    seed, step_org = aliased(Org), aliased(Org)
    name = f"partof_{direction}_{next(_cte_names)}"
    if direction == "below":
        tree = (
            select(seed.organization_id.label("oid"), literal(1).label("depth"))
            .where(seed.partof_id == x, seed.tenant_id == ctx.tenant_id)
            .cte(name=name, recursive=True)
        )
        tree = tree.union_all(
            select(step_org.organization_id, tree.c.depth + 1).where(
                step_org.partof_id == tree.c.oid, step_org.tenant_id == ctx.tenant_id, tree.c.depth < max_depth
            )
        )
        return Org.organization_id.in_(select(tree.c.oid))
    tree = (
        select(seed.organization_id.label("oid"), seed.partof_id.label("pid"), literal(1).label("depth"))
        .where(seed.organization_id == x, seed.tenant_id == ctx.tenant_id)
        .cte(name=name, recursive=True)
    )
    tree = tree.union_all(
        select(step_org.organization_id, step_org.partof_id, tree.c.depth + 1).where(
            step_org.organization_id == tree.c.pid, step_org.tenant_id == ctx.tenant_id, tree.c.depth < max_depth
        )
    )
    return or_(Org.partof_id == x, Org.partof_id.in_(select(tree.c.oid)))


def _partof_chain(target, inner, ctx):
    """`partof.<param>=v`: partOf points at an Organization (same tenant)
    matching `<param>=v`. The subquery deliberately doesn't correlate to
    the outer organization row — it ranges over the referenced one."""
    referenced = (
        select(Org.organization_id).where(Org.tenant_id == ctx.tenant_id, inner).correlate(None)
    )
    return Org.partof_id.in_(referenced)


_E = OrganizationEndpoint


def _endpoint_match(value, modifier, ctx):
    if modifier == "identifier":
        return _exists(
            _E, token_condition(_E.reference_identifier_system, _E.reference_identifier_value, parse_token(value))
        )
    return _exists(
        _E,
        reference_match(
            _E.reference_type, _E.reference_id, _E.reference_reference, value, modifier, ctx,
            ("Endpoint",), OrganizationEndpointReferenceType,
        ),
    )


# ── _include / _revinclude ───────────────────────────────────────────────────


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


async def _include_partof(session, ctx, orgs):
    """_include=Organization:partof — the parents of these organizations."""
    parents = {o.partof_id for o in orgs if o.partof_id is not None}
    if not parents:
        return []
    return await _fetch(
        session, select(Org).where(Org.tenant_id == ctx.tenant_id, Org.organization_id.in_(parents))
    )


async def _revinclude_partof(session, ctx, orgs):
    """_revinclude=Organization:partof — the children of these organizations."""
    ids = {o.organization_id for o in orgs}
    return await _fetch(session, select(Org).where(Org.tenant_id == ctx.tenant_id, Org.partof_id.in_(ids)))


async def _revinclude_location_organization(session, ctx, orgs):
    """_revinclude=Location:organization — Locations whose
    managingOrganization is one of these organizations."""
    from app.models.location import LocationModel as Loc

    ids = {o.organization_id for o in orgs}
    return await _fetch(
        session, select(Loc).where(Loc.tenant_id == ctx.tenant_id, Loc.managing_organization_id.in_(ids))
    )


def _register_kind() -> None:
    """How the search engine identifies and renders Organization rows —
    for Organization searches and for Organizations included by others."""
    from app.fhir.mappers.organization import to_fhir_organization
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind("Organization", lambda o: o.organization_id, to_fhir_organization, "organizations")
    )


# ── registry ─────────────────────────────────────────────────────────────────

_city, _city_present = _address_part("city")
_state, _state_present = _address_part("state")
_country, _country_present = _address_part("country")
_postal, _postal_present = _address_part("postal_code")

_STRING = frozenset({"exact", "contains", "missing"})


@cache
def organization_search() -> SearchRegistry:
    _register_kind()
    params = [
        SearchParam(
            "_id", "token", "Logical id of the resource (the public organization id)", "Resource.id",
            _id_match, lambda ctx: true(), frozenset({"not", "missing"}),
            sort=lambda: Org.organization_id, example="190001",
        ),
        SearchParam(
            "_lastUpdated", "date", "When the resource last changed (meta.lastUpdated)", "Resource.meta.lastUpdated",
            lambda v, m, ctx: date_match(last_updated(), v), lambda ctx: true(),
            sort=last_updated, example="ge2024-01-01",
        ),
        SearchParam(
            "active", "token", "Is the Organization record active", "Organization.active",
            _active_match, lambda ctx: Org.active.is_not(None), frozenset({"not", "missing"}),
            sort=lambda: Org.active, example="true",
            modifier_docs={"not": "`:not` — active is not this value, or is not recorded at all."},
        ),
        SearchParam(
            "address", "string",
            "A server defined search that may match any of the string fields in the Address, including line, "
            "city, district, state, country, postalCode, and/or text",
            "Organization.address", _address_match, lambda ctx: _exists(_A), _STRING, example="Main St",
        ),
        SearchParam(
            "address-city", "string", "A city specified in an address", "Organization.address.city",
            _city, _city_present, _STRING, sort=lambda: _child_sort(_A.city_norm, _A), example="Boston",
        ),
        SearchParam(
            "address-country", "string", "A country specified in an address", "Organization.address.country",
            _country, _country_present, _STRING, sort=lambda: _child_sort(_A.country_norm, _A), example="US",
        ),
        SearchParam(
            "address-postalcode", "string", "A postal code specified in an address", "Organization.address.postalCode",
            _postal, _postal_present, _STRING, sort=lambda: _child_sort(_A.postal_code_norm, _A), example="02110",
        ),
        SearchParam(
            "address-state", "string", "A state specified in an address", "Organization.address.state",
            _state, _state_present, _STRING, sort=lambda: _child_sort(_A.state_norm, _A), example="MA",
        ),
        SearchParam(
            "address-use", "token",
            "A use code specified in an address (home | work | temp | old | billing; system "
            f"{_ADDRESS_USE_SYSTEM})",
            "Organization.address.use", _address_use_match, lambda ctx: _exists(_A, _A.use.is_not(None)),
            frozenset({"not", "missing"}), example="work",
        ),
        SearchParam(
            "endpoint", "reference", "Technical endpoints providing access to services operated for the organization",
            "Organization.endpoint", _endpoint_match, lambda ctx: _exists(_E), frozenset({"identifier", "missing"}),
            targets=("Endpoint",), example="Endpoint/1",
        ),
        SearchParam(
            "identifier", "token", "Any identifier for the organization (not the accreditation issuer's identifier)",
            "Organization.identifier", _identifier_match, lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I), example="http://hl7.org/fhir/sid/us-npi|1234567893",
            modifier_docs={"text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."},
        ),
        SearchParam(
            "name", "string", "A portion of the organization's name or alias", "Organization.name | Organization.alias",
            _name_match, lambda ctx: or_(Org.name.is_not(None), Org.alias.is_not(None)), _STRING,
            sort=_name_sort, example="General",
        ),
        SearchParam(
            "partof", "reference", "An organization of which this organization forms a part", "Organization.partOf",
            _partof_match, _partof_present, frozenset({"identifier", "above", "below", "missing"}),
            targets=("Organization",), chain=_partof_chain, chain_targets={"Organization": organization_search},
            hierarchy=_partof_hierarchy, sort=lambda: Org.partof_id, example="Organization/190001",
            modifier_docs={
                "below": "`:below` — organizations anywhere below the given one in the partOf hierarchy (children, grandchildren, ...).",
                "above": "`:above` — organizations whose partOf is the given one or any of its ancestors.",
            },
        ),
        SearchParam(
            "phonetic", "string",
            "A portion of the organization's name using some kind of phonetic matching algorithm "
            "(American Soundex, word by word; the first letter must match)",
            "Organization.name", _phonetic_match, lambda ctx: Org.name_phonetic.is_not(None),
            sort=lambda: Org.name_phonetic, example="Generel Hospitel",
        ),
        SearchParam(
            "type", "token", "A code for the type of organization", "Organization.type",
            _type_match, lambda ctx: _exists(_T), frozenset({"text", "not", "in", "not-in", "above", "below", "missing"}),
            sort=lambda: _child_sort(_T.code, _T),
            example="http://terminology.hl7.org/CodeSystem/organization-type|prov",
        ),
    ]
    return SearchRegistry(
        resource_type="Organization",
        params={p.name: p for p in params},
        summary_elements=frozenset({"identifier", "active", "type", "name", "partOf"}),
        includes=(
            IncludeTarget("Organization", "partof", "Organization", _include_partof),
            # Endpoint isn't a resource on this server: accepted, adds nothing.
            IncludeTarget("Organization", "endpoint", "Endpoint"),
        ),
        revincludes=(
            IncludeTarget("Organization", "partof", "Organization", _revinclude_partof, reverse=True),
            IncludeTarget("Location", "organization", "Organization", _revinclude_location_organization, reverse=True),
        ),
        default_sort=lambda: [Org.organization_id.desc()],
    )
