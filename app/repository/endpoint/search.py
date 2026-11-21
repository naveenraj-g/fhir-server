"""
FHIR R4 Endpoint search parameters
(https://www.hl7.org/fhir/R4/endpoint.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
endpoint_search() below. Same arrangement as
app.repository.organization.search.

Each parameter's SQL reads only the search index (EndpointModel's columns and
child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

from functools import cache

from sqlalchemy import exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
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
from app.models.endpoint import (
    EndpointIdentifier,
    EndpointModel,
    EndpointPayloadType,
    EndpointStatus,
)
from app.models.enums import OrganizationReferenceType

E = EndpointModel
_I = EndpointIdentifier
_P = EndpointPayloadType
_STATUS_SYSTEM = "http://hl7.org/fhir/endpoint-status"


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(select(literal(1)).where(model.endpoint_pk == E.id, *conditions))


def _child_sort(column, model):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return select(fn(column)).where(model.endpoint_pk == E.id).scalar_subquery()

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(E.updated_at, E.created_at)


# ── _id / status / name ──────────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return E.endpoint_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to one code system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an
    unknown code matches nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return E.status.is_not(None)
    try:
        return E.status == EndpointStatus(token.code)
    except ValueError:
        return false()


def _name_match(value, modifier, ctx):
    return string_match(E.name, E.name_norm, value, modifier)


# ── identifier / connection-type / payload-type ──────────────────────────────


def _identifier_match(value, modifier, ctx):
    if modifier == "text":
        return _exists(
            _I, token_text_match((_I.type_text_norm, _I.type_display_norm), value)
        )
    if modifier == "of-type":
        type_system, type_code, ident = parse_of_type(value)
        return _exists(
            _I,
            _I.type_system == type_system,
            _I.type_code == type_code,
            _I.value == ident,
        )
    return _exists(_I, token_match(_I.system, _I.value, value))


def _connection_type_match(value, modifier, ctx):
    # connectionType is a single Coding: `:text` searches its display.
    return coded_token_match(
        E.connection_type_system,
        E.connection_type_code,
        value,
        modifier,
        (E.connection_type_display_norm,),
    )


def _payload_type_match(value, modifier, ctx):
    return _exists(
        _P,
        coded_token_match(
            _P.system, _P.code, value, modifier, (_P.text_norm, _P.display_norm)
        ),
    )


# ── organization (managingOrganization) ──────────────────────────────────────


def _organization_match(value, modifier, ctx):
    if modifier == "identifier":
        return token_condition(
            E.managing_organization_identifier_system,
            E.managing_organization_identifier_value,
            parse_token(value),
        )
    return reference_match(
        E.managing_organization_type,
        E.managing_organization_id,
        E.managing_organization_reference,
        value,
        modifier,
        ctx,
        ("Organization",),
        OrganizationReferenceType,
    )


def _organization_present(ctx):
    return or_(
        E.managing_organization_reference.is_not(None),
        E.managing_organization_identifier_value.is_not(None),
    )


def _organization_chain(target, inner, ctx):
    """`organization.<param>=v`: managingOrganization is an Organization
    (same tenant) matching any Organization search parameter. The subquery
    doesn't correlate to the outer row — it ranges over the referenced
    Organization."""
    from app.models.organization import OrganizationModel as Org

    referenced = (
        select(Org.organization_id)
        .where(Org.tenant_id == ctx.tenant_id, inner)
        .correlate(None)
    )
    return E.managing_organization_id.in_(referenced)


def _organization_search():
    from app.repository.organization.search import organization_search

    return organization_search()


# ── _include / _revinclude ───────────────────────────────────────────────────


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


async def _include_organization(session, ctx, endpoints):
    """_include=Endpoint:organization — the managing organizations."""
    from app.models.organization import OrganizationModel as Org

    ids = {
        e.managing_organization_id
        for e in endpoints
        if e.managing_organization_id is not None
    }
    if not ids:
        return []
    return await _fetch(
        session,
        select(Org).where(Org.tenant_id == ctx.tenant_id, Org.organization_id.in_(ids)),
    )


async def _revinclude_organization_endpoint(session, ctx, endpoints):
    """_revinclude=Organization:endpoint — Organizations whose `endpoint`
    points at one of these endpoints."""
    from app.models.organization import OrganizationEndpoint as Ref
    from app.models.organization import OrganizationModel as Org

    ids = {e.endpoint_id for e in endpoints}
    pks = select(Ref.organization_pk).where(Ref.reference_id.in_(ids))
    return await _fetch(
        session, select(Org).where(Org.tenant_id == ctx.tenant_id, Org.id.in_(pks))
    )


async def _revinclude_location_endpoint(session, ctx, endpoints):
    """_revinclude=Location:endpoint — Locations whose `endpoint` points at
    one of these endpoints."""
    from app.models.location import LocationEndpoint as Ref
    from app.models.location import LocationModel as Loc

    ids = {e.endpoint_id for e in endpoints}
    pks = select(Ref.location_pk).where(Ref.reference_id.in_(ids))
    return await _fetch(
        session, select(Loc).where(Loc.tenant_id == ctx.tenant_id, Loc.id.in_(pks))
    )


async def _revinclude_healthcare_service_endpoint(session, ctx, endpoints):
    """_revinclude=HealthcareService:endpoint — HealthcareServices whose
    `endpoint` points at one of these endpoints."""
    from app.models.healthcare_service import HealthcareServiceModel as HS
    from app.models.healthcare_service import HealthcareServiceReference as Ref

    ids = {e.endpoint_id for e in endpoints}
    pks = select(Ref.healthcare_service_pk).where(
        Ref.param == "endpoint", Ref.reference_id.in_(ids)
    )
    return await _fetch(
        session, select(HS).where(HS.tenant_id == ctx.tenant_id, HS.id.in_(pks))
    )


def _revinclude_practitioner_roles(param: str, key):
    """_revinclude=PractitionerRole:<param> — roles whose `{param}` reference
    points at one of these rows (matched on the public id `key(row)`)."""

    async def fetch(session, ctx, rows):
        from app.models.practitioner_role import PractitionerRoleModel as PR
        from app.models.practitioner_role import PractitionerRoleReference as Ref

        ids = {key(r) for r in rows}
        pks = select(Ref.practitioner_role_pk).where(
            Ref.param == param, Ref.reference_id.in_(ids)
        )
        return await _fetch(
            session, select(PR).where(PR.tenant_id == ctx.tenant_id, PR.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Endpoint rows — for
    Endpoint searches and for Endpoints included by others."""
    from app.fhir.mappers.endpoint import to_fhir_endpoint
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind("Endpoint", lambda e: e.endpoint_id, to_fhir_endpoint, "endpoints")
    )


# ── registry ─────────────────────────────────────────────────────────────────

_STRING = frozenset({"exact", "contains", "missing"})
_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})


@cache
def endpoint_search() -> SearchRegistry:
    _register_kind()
    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public endpoint id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: E.endpoint_id,
            example="620001",
        ),
        SearchParam(
            "_lastUpdated",
            "date",
            "When the resource last changed (meta.lastUpdated)",
            "Resource.meta.lastUpdated",
            lambda v, m, ctx: date_match(last_updated(), v),
            lambda ctx: true(),
            sort=last_updated,
            example="ge2024-01-01",
        ),
        SearchParam(
            "connection-type",
            "token",
            "Protocol/Profile/Standard to be used with this endpoint connection",
            "Endpoint.connectionType",
            _connection_type_match,
            lambda ctx: E.connection_type_code.is_not(None),
            _TOKEN,
            sort=lambda: E.connection_type_code,
            example="http://terminology.hl7.org/CodeSystem/endpoint-connection-type|hl7-fhir-rest",
        ),
        SearchParam(
            "identifier",
            "token",
            "Identifies this endpoint across multiple systems",
            "Endpoint.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:endpoints|EP-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "name",
            "string",
            "A name that this endpoint can be identified by",
            "Endpoint.name",
            _name_match,
            lambda ctx: E.name.is_not(None),
            _STRING,
            sort=lambda: E.name_norm,
            example="Hospital FHIR API",
        ),
        SearchParam(
            "organization",
            "reference",
            "The organization that is managing the endpoint",
            "Endpoint.managingOrganization",
            _organization_match,
            _organization_present,
            frozenset({"identifier", "missing"}),
            targets=("Organization",),
            chain=_organization_chain,
            chain_targets={"Organization": _organization_search},
            sort=lambda: E.managing_organization_id,
            example="Organization/190001",
        ),
        SearchParam(
            "payload-type",
            "token",
            "The type of content that may be used at this endpoint (e.g. XDS Discharge summaries)",
            "Endpoint.payloadType",
            _payload_type_match,
            lambda ctx: _exists(_P),
            _TOKEN,
            sort=lambda: _child_sort(_P.code, _P),
            example="http://terminology.hl7.org/CodeSystem/endpoint-payload-type|any",
        ),
        SearchParam(
            "status",
            "token",
            f"The current status of the Endpoint (active | suspended | error | off | entered-in-error | test; system {_STATUS_SYSTEM})",
            "Endpoint.status",
            _status_match,
            lambda ctx: E.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: E.status,
            example="active",
        ),
    ]

    return SearchRegistry(
        resource_type="Endpoint",
        params={p.name: p for p in params},
        # Σ elements in the R4 Endpoint definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "status",
                "connectionType",
                "name",
                "managingOrganization",
                "period",
                "payloadType",
                "payloadMimeType",
                "address",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset(
            {"status", "connectionType", "payloadType", "address"}
        ),
        includes=(
            IncludeTarget(
                "Endpoint", "organization", "Organization", _include_organization
            ),
        ),
        revincludes=(
            IncludeTarget(
                "Organization",
                "endpoint",
                "Endpoint",
                _revinclude_organization_endpoint,
                reverse=True,
            ),
            IncludeTarget(
                "Location",
                "endpoint",
                "Endpoint",
                _revinclude_location_endpoint,
                reverse=True,
            ),
            IncludeTarget(
                "HealthcareService",
                "endpoint",
                "Endpoint",
                _revinclude_healthcare_service_endpoint,
                reverse=True,
            ),
            IncludeTarget(
                "PractitionerRole",
                "endpoint",
                "Endpoint",
                _revinclude_practitioner_roles("endpoint", lambda e: e.endpoint_id),
                reverse=True,
            ),
        ),
        default_sort=lambda: [E.endpoint_id.desc()],
    )
