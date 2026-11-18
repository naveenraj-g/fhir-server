"""
FHIR R4 HealthcareService search parameters
(https://www.hl7.org/fhir/R4/healthcareservice.html#search) plus the common
`_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL,
`_sort`, `_include`, and the OpenAPI docs all come from
healthcare_service_search() below. Same arrangement as
app.repository.organization.search.

Each parameter's SQL reads only the search index (HealthcareServiceModel's
columns and child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

from functools import cache

from sqlalchemy import exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchError, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    coded_token_match,
    date_match,
    reference_match,
    string_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.models.enums import OrganizationReferenceType
from app.models.healthcare_service import (
    HealthcareServiceIdentifier,
    HealthcareServiceModel,
    HealthcareServiceReference,
    HealthcareServiceToken,
)

HS = HealthcareServiceModel
_I = HealthcareServiceIdentifier
_Tk = HealthcareServiceToken
_R = HealthcareServiceReference


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(select(literal(1)).where(model.healthcare_service_pk == HS.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.healthcare_service_pk == HS.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(HS.updated_at, HS.created_at)


# ── _id / active / name ──────────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system or not (token.code or "").isdigit():  # ids are the numeric public id
        return false()
    return HS.healthcare_service_id == int(token.code)


def _active_match(value, modifier, ctx):
    token = parse_token(value)
    if token.code not in ("true", "false") or token.system:  # boolean: no code system
        raise SearchError(value, f"'active' takes true or false, not '{value}'.")
    return HS.active.is_(token.code == "true")


def _name_match(value, modifier, ctx):
    return string_match(HS.name, HS.name_norm, value, modifier)


# ── identifier ───────────────────────────────────────────────────────────────


def _identifier_match(value, modifier, ctx):
    if modifier == "text":
        return _exists(_I, token_text_match((_I.type_text_norm, _I.type_display_norm), value))
    if modifier == "of-type":
        type_system, type_code, ident = parse_of_type(value)
        return _exists(_I, _I.type_system == type_system, _I.type_code == type_code, _I.value == ident)
    return _exists(_I, token_match(_I.system, _I.value, value))


# ── the five CodeableConcept token parameters ────────────────────────────────


def _token_param(param: str):
    """(match, present, sort) for one of the token parameters held in the
    shared token table, selected by its `param` value."""

    def match(value, modifier, ctx):
        return _exists(
            _Tk,
            _Tk.param == param,
            coded_token_match(_Tk.system, _Tk.code, value, modifier, (_Tk.text_norm, _Tk.display_norm)),
        )

    def present(ctx):
        return _exists(_Tk, _Tk.param == param)

    def sort():
        return _child_sort(_Tk.code, _Tk, _Tk.param == param)

    return match, present, sort


# ── references ───────────────────────────────────────────────────────────────


def _organization_match(value, modifier, ctx):
    if modifier == "identifier":
        return token_condition(
            HS.provided_by_identifier_system, HS.provided_by_identifier_value, parse_token(value)
        )
    return reference_match(
        HS.provided_by_type, HS.provided_by_id, HS.provided_by_reference,
        value, modifier, ctx, ("Organization",), OrganizationReferenceType,
    )


def _organization_present(ctx):
    return or_(HS.provided_by_reference.is_not(None), HS.provided_by_identifier_value.is_not(None))


def _organization_chain(target, inner, ctx):
    """`organization.<param>=v`: providedBy is an Organization (same tenant)
    matching any Organization search parameter. The subquery doesn't
    correlate to the outer row — it ranges over the referenced Organization."""
    from app.models.organization import OrganizationModel as Org

    referenced = select(Org.organization_id).where(Org.tenant_id == ctx.tenant_id, inner).correlate(None)
    return HS.provided_by_id.in_(referenced)


def _reference_param(param: str, resource_type: str):
    """(match, present, chain, sort) for one of the 0..* reference parameters
    held in the shared reference table, selected by its `param` value."""

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return _exists(
                _R,
                _R.param == param,
                token_condition(_R.reference_identifier_system, _R.reference_identifier_value, parse_token(value)),
            )
        return _exists(
            _R,
            _R.param == param,
            # reference_type is a plain string here (the value is fixed by `param`).
            reference_match(
                _R.reference_type, _R.reference_id, _R.reference_reference,
                value, modifier, ctx, (resource_type,), str,
            ),
        )

    def present(ctx):
        return _exists(
            _R,
            _R.param == param,
            or_(_R.reference_reference.is_not(None), _R.reference_identifier_value.is_not(None)),
        )

    def chain(target, inner, ctx):
        """`<param>.<p>=v`: some referenced Location (same tenant) matches
        `<p>=v`."""
        from app.models.location import LocationModel as Loc

        referenced = select(Loc.location_id).where(Loc.tenant_id == ctx.tenant_id, inner).correlate(None)
        return _exists(_R, _R.param == param, _R.reference_id.in_(referenced))

    def sort():
        return _child_sort(_R.reference_id, _R, _R.param == param)

    return match, present, chain, sort


# ── _include ─────────────────────────────────────────────────────────────────


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


async def _include_organization(session, ctx, services):
    """_include=HealthcareService:organization — the providing organizations."""
    from app.models.organization import OrganizationModel as Org

    ids = {s.provided_by_id for s in services if s.provided_by_id is not None}
    if not ids:
        return []
    return await _fetch(session, select(Org).where(Org.tenant_id == ctx.tenant_id, Org.organization_id.in_(ids)))


def _include_locations(param: str):
    async def fetch(session, ctx, services):
        from app.models.location import LocationModel as Loc

        pks = {s.id for s in services}
        referenced = select(_R.reference_id).where(
            _R.healthcare_service_pk.in_(pks), _R.param == param, _R.reference_id.is_not(None)
        )
        return await _fetch(session, select(Loc).where(Loc.tenant_id == ctx.tenant_id, Loc.location_id.in_(referenced)))

    return fetch


async def _include_endpoint(session, ctx, services):
    """_include=HealthcareService:endpoint — the endpoints these services
    point at (only those that are Endpoint resources on this server)."""
    from app.models.endpoint import EndpointModel as Ep

    ids = select(_R.reference_id).where(
        _R.healthcare_service_pk.in_({s.id for s in services}), _R.param == "endpoint", _R.reference_id.is_not(None)
    )
    return await _fetch(session, select(Ep).where(Ep.tenant_id == ctx.tenant_id, Ep.endpoint_id.in_(ids)))


def _register_kind() -> None:
    """How the search engine identifies and renders HealthcareService rows."""
    from app.fhir.mappers.healthcare_service import to_fhir_healthcare_service
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "HealthcareService",
            lambda s: s.healthcare_service_id,
            to_fhir_healthcare_service,
            "healthcare-services",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_STRING = frozenset({"exact", "contains", "missing"})
_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})


def _location_search():
    from app.repository.location.search import location_search

    return location_search()


def _organization_search():
    from app.repository.organization.search import organization_search

    return organization_search()


@cache
def healthcare_service_search() -> SearchRegistry:
    _register_kind()

    def token(name, description, expression, example):
        match, present, sort = _token_param(name)
        return SearchParam(name, "token", description, expression, match, present, _TOKEN, sort=sort, example=example)

    def reference(name, description, expression, example, resource_type):
        match, present, chain, sort = _reference_param(name, resource_type)
        return SearchParam(
            name, "reference", description, expression, match, present,
            frozenset({"identifier", "missing"}), targets=(resource_type,),
            chain=chain if resource_type == "Location" else None,
            chain_targets={"Location": _location_search} if resource_type == "Location" else {},
            sort=sort, example=example,
        )

    params = [
        SearchParam(
            "_id", "token", "Logical id of the resource (the public healthcare service id)", "Resource.id",
            _id_match, lambda ctx: true(), frozenset({"not", "missing"}),
            sort=lambda: HS.healthcare_service_id, example="150001",
        ),
        SearchParam(
            "_lastUpdated", "date", "When the resource last changed (meta.lastUpdated)", "Resource.meta.lastUpdated",
            lambda v, m, ctx: date_match(last_updated(), v), lambda ctx: true(),
            sort=last_updated, example="ge2024-01-01",
        ),
        SearchParam(
            "active", "token", "The Healthcare Service is currently marked as active", "HealthcareService.active",
            _active_match, lambda ctx: HS.active.is_not(None), frozenset({"not", "missing"}),
            sort=lambda: HS.active, example="true",
            modifier_docs={"not": "`:not` — active is not this value, or is not recorded at all."},
        ),
        token(
            "characteristic", "One of the HealthcareService's characteristics",
            "HealthcareService.characteristic", "http://example.org/chars|wheelchair",
        ),
        reference(
            "coverage-area", "Location(s) service is intended for/available to",
            "HealthcareService.coverageArea", "Location/230001", "Location",
        ),
        reference(
            "endpoint", "Technical endpoints providing access to electronic services operated for the healthcare service",
            "HealthcareService.endpoint", "Endpoint/1", "Endpoint",
        ),
        SearchParam(
            "identifier", "token", "External identifiers for this item", "HealthcareService.identifier",
            _identifier_match, lambda ctx: _exists(_I), frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I), example="urn:facility|12345",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        reference(
            "location", "The location of the Healthcare Service", "HealthcareService.location",
            "Location/230001", "Location",
        ),
        SearchParam(
            "name", "string", "A portion of the Healthcare service name", "HealthcareService.name",
            _name_match, lambda ctx: HS.name.is_not(None), _STRING,
            sort=lambda: HS.name_norm, example="Cardiology",
        ),
        SearchParam(
            "organization", "reference", "The organization providing the Healthcare service",
            "HealthcareService.providedBy", _organization_match, _organization_present,
            frozenset({"identifier", "missing"}), targets=("Organization",),
            chain=_organization_chain, chain_targets={"Organization": _organization_search},
            sort=lambda: HS.provided_by_id, example="Organization/190001",
        ),
        token(
            "program", "One of the Programs supported by this HealthcareService",
            "HealthcareService.program", "http://example.org/programs|diabetes",
        ),
        token(
            "service-category", "Service Category of the Healthcare Service", "HealthcareService.category",
            "http://terminology.hl7.org/CodeSystem/service-category|35",
        ),
        token(
            "service-type", "The type of service provided by this healthcare service", "HealthcareService.type",
            "http://terminology.hl7.org/CodeSystem/service-type|124",
        ),
        token(
            "specialty", "The specialty of the service provided by this healthcare service",
            "HealthcareService.specialty", "http://snomed.info/sct|394579002",
        ),
    ]

    return SearchRegistry(
        resource_type="HealthcareService",
        params={p.name: p for p in params},
        # Σ elements in the R4 HealthcareService definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {"identifier", "active", "providedBy", "category", "type", "specialty", "location", "name", "comment", "photo"}
        ),
        mandatory_elements=frozenset(),
        includes=(
            IncludeTarget("HealthcareService", "organization", "Organization", _include_organization),
            IncludeTarget("HealthcareService", "location", "Location", _include_locations("location")),
            IncludeTarget("HealthcareService", "coverage-area", "Location", _include_locations("coverage-area")),
            IncludeTarget("HealthcareService", "endpoint", "Endpoint", _include_endpoint),
        ),
        # Nothing that references a HealthcareService is on the engine yet
        # (PractitionerRole, Schedule, ... will add their _revinclude here).
        revincludes=(),
        default_sort=lambda: [HS.healthcare_service_id.desc()],
    )
