"""
FHIR R4 AppointmentResponse search parameters
(https://www.hl7.org/fhir/R4/appointmentresponse.html#search) plus the common
`_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL,
`_sort`, `_include` / `_revinclude`, and the OpenAPI docs all come from
appointment_response_search() below. Same arrangement as
app.repository.appointment.search (multi-target actor) and
app.repository.slot.search (a reference held as columns on the row).

Each parameter's SQL reads only the search index (AppointmentResponseModel's
columns and child table, see its docstring) — never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    date_match,
    reference_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.models.appointment_response import (
    ACTOR_TYPES,
    AppointmentResponseIdentifier,
    AppointmentResponseModel,
    AppointmentResponseParticipantStatus,
)
from app.repository._search_targets import MODELED

R = AppointmentResponseModel
_I = AppointmentResponseIdentifier
_PARTICIPATION_STATUS_SYSTEM = "http://hl7.org/fhir/participationstatus"

# Every rebuilt resource type this server can chain through and `_include`: derived from
# RESOURCE_REGISTRY by app/repository/_search_targets.py, so there is no list to keep here.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = MODELED


def _model(resource_type: str):
    module, cls, id_col, *_ = _MODELED[resource_type]
    model = getattr(importlib.import_module(module), cls)
    return model, getattr(model, id_col)


def _registry_of(resource_type: str):
    def get():
        _m, _c, _i, module, factory = _MODELED[resource_type]
        return getattr(importlib.import_module(module), factory)()

    return get


def _exists(model, *conditions):
    """Correlated EXISTS against the identifier child table."""
    return exists(
        select(literal(1)).where(model.appointment_response_pk == R.id, *conditions)
    )


def last_updated():
    return func.coalesce(R.updated_at, R.created_at)


# ── _id / part-status ────────────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return R.appointment_response_id == int(token.code)


def _part_status_match(value, modifier, ctx):
    """`part-status` is a `code` bound to the participation-status system:
    `code` or `system|code`; another system or `|code` (no system) never
    matches; an unknown code matches nothing (rather than failing the Postgres
    enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _PARTICIPATION_STATUS_SYSTEM:
        return false()
    if token.code is None:
        return R.participant_status.is_not(None)
    try:
        return R.participant_status == AppointmentResponseParticipantStatus(token.code)
    except ValueError:
        return false()


# ── identifier ───────────────────────────────────────────────────────────────


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


def _identifier_sort():
    def agg(fn):
        return (
            select(fn(_I.value))
            .where(_I.appointment_response_pk == R.id)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


# ── actor / patient / practitioner / location ────────────────────────────────


def _actor_param(targets: tuple[str, ...]):
    """(match, present, chain) for `actor` (all seven types) or one of its
    narrowed forms (`patient`, `practitioner`, `location` — the actor resolves
    to that single type). All read the actor_* columns."""
    narrowed = targets[0] if len(targets) == 1 else None
    # `is_not(None)` keeps `NOT present` (`:missing=true`) from going NULL for a row whose
    # actor has no resolved type (a logical, identifier-only reference).
    type_filter = (
        (R.actor_type.is_not(None), R.actor_type == narrowed) if narrowed else ()
    )

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return token_condition(
                R.actor_identifier_system, R.actor_identifier_value, parse_token(value)
            )
        # `modifier` is a target type (actor:Practitioner=30001) or None; a bare
        # id with several targets is ambiguous and is rejected by
        # reference_target(). actor_type is a plain string here.
        return reference_match(
            R.actor_type,
            R.actor_id,
            R.actor_reference,
            value,
            modifier,
            ctx,
            targets,
            str,
        )

    def present(ctx):
        return and_(
            or_(R.actor_reference.is_not(None), R.actor_identifier_value.is_not(None)),
            *type_filter,
        )

    def chain(target, inner, ctx):
        """`actor:<Type>.<p>=v`: the actor, when it is of that type (same
        tenant), matches `<p>=v`."""
        model, id_col = _model(target)
        referenced = (
            select(id_col)
            .where(model.tenant_id == ctx.tenant_id, inner)
            .correlate(None)
        )
        return (R.actor_type == target) & R.actor_id.in_(referenced)

    return match, present, chain


# ── appointment ──────────────────────────────────────────────────────────────


def _appointment_match(value, modifier, ctx):
    if modifier == "identifier":
        return token_condition(
            R.appointment_identifier_system,
            R.appointment_identifier_value,
            parse_token(value),
        )
    return reference_match(
        R.appointment_type,
        R.appointment_id,
        R.appointment_reference,
        value,
        modifier,
        ctx,
        ("Appointment",),
        str,
    )


def _appointment_present(ctx):
    return or_(
        R.appointment_reference.is_not(None),
        R.appointment_identifier_value.is_not(None),
    )


def _appointment_chain(target, inner, ctx):
    """`appointment.<param>=v`: the Appointment (same tenant) matches any
    Appointment search parameter (e.g. `appointment.status=booked`,
    `appointment.actor:Practitioner.family=Careful`)."""
    model, id_col = _model("Appointment")
    referenced = (
        select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)
    )
    return (R.appointment_type == "Appointment") & R.appointment_id.in_(referenced)


# ── _include / _revinclude ───────────────────────────────────────────────────


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


def _include_actors(resource_type: str):
    """_include=AppointmentResponse:actor[:Type] (and :patient / :practitioner /
    :location) — the actors of one type these responses point at (only types
    that are resources on this server)."""

    async def fetch(session, ctx, responses):
        model, id_col = _model(resource_type)
        ids = {
            r.actor_id
            for r in responses
            if r.actor_type == resource_type and r.actor_id is not None
        }
        if not ids:
            return []
        return await _fetch(
            session,
            select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids)),
        )

    return fetch


async def _include_appointment(session, ctx, responses):
    """_include=AppointmentResponse:appointment — the appointments these
    responses reply to."""
    model, id_col = _model("Appointment")
    ids = {r.appointment_id for r in responses if r.appointment_id is not None}
    if not ids:
        return []
    return await _fetch(
        session, select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids))
    )


def revinclude_responses_via_actor(resource_type: str, key):
    """_revinclude=AppointmentResponse:actor / :patient / :practitioner /
    :location — responses whose actor is of this type and points at one of
    these rows (matched on the public id `key(row)`). Declared on the registry
    of each actor type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        return await _fetch(
            session,
            select(R).where(
                R.tenant_id == ctx.tenant_id,
                R.actor_type == resource_type,
                R.actor_id.in_(ids),
            ),
        )

    return fetch


def revinclude_responses_via_appointment(key):
    """_revinclude=AppointmentResponse:appointment — responses replying to one
    of these appointments."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        return await _fetch(
            session,
            select(R).where(
                R.tenant_id == ctx.tenant_id,
                R.appointment_type == "Appointment",
                R.appointment_id.in_(ids),
            ),
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders AppointmentResponse rows."""
    from app.fhir.mappers.appointment_response import to_fhir_appointment_response
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "AppointmentResponse",
            lambda r: r.appointment_response_id,
            to_fhir_appointment_response,
            "appointment-responses",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_REFERENCE = frozenset({"identifier", "missing"})


@cache
def appointment_response_search() -> SearchRegistry:
    _register_kind()

    def actor(name, description, expression, targets, example):
        match, present, chain = _actor_param(targets)
        modeled = [t for t in targets if t in _MODELED]
        return SearchParam(
            name,
            "reference",
            description,
            expression,
            match,
            present,
            _REFERENCE,
            targets=targets,
            chain=chain,
            chain_targets={t: _registry_of(t) for t in modeled},
            sort=lambda: R.actor_id,
            example=example,
            modifier_docs={
                "identifier": "`:identifier` — match the logical identifier of an actor that has no resource here."
            },
        )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public appointment response id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: R.appointment_response_id,
            example="370001",
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
        actor(
            "actor",
            "The Person, Location/HealthcareService or Device that this appointment response replies for",
            "AppointmentResponse.actor",
            ACTOR_TYPES,
            "Practitioner/30001",
        ),
        SearchParam(
            "appointment",
            "reference",
            "The appointment that the response is attached to",
            "AppointmentResponse.appointment",
            _appointment_match,
            _appointment_present,
            _REFERENCE,
            targets=("Appointment",),
            chain=_appointment_chain,
            chain_targets={"Appointment": _registry_of("Appointment")},
            sort=lambda: R.appointment_id,
            example="Appointment/40001",
        ),
        SearchParam(
            "identifier",
            "token",
            "An Identifier in this appointment response",
            "AppointmentResponse.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=_identifier_sort,
            example="urn:appointment-responses|AR-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        actor(
            "location",
            "This Response is for this Location",
            "AppointmentResponse.actor.where(resolve() is Location)",
            ("Location",),
            "Location/230001",
        ),
        SearchParam(
            "part-status",
            "token",
            "The participants acceptance status for this appointment (accepted | declined | tentative | "
            f"needs-action; system {_PARTICIPATION_STATUS_SYSTEM})",
            "AppointmentResponse.participantStatus",
            _part_status_match,
            lambda ctx: R.participant_status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: R.participant_status,
            example="accepted",
        ),
        actor(
            "patient",
            "This Response is for this Patient",
            "AppointmentResponse.actor.where(resolve() is Patient)",
            ("Patient",),
            "Patient/10001",
        ),
        actor(
            "practitioner",
            "This Response is for this Practitioner",
            "AppointmentResponse.actor.where(resolve() is Practitioner)",
            ("Practitioner",),
            "Practitioner/30001",
        ),
    ]

    actor_includes = tuple(
        IncludeTarget("AppointmentResponse", "actor", t, _include_actors(t))
        for t in ACTOR_TYPES
        if t in _MODELED
        if t != "Appointment"
    )
    narrowed_includes = tuple(
        IncludeTarget("AppointmentResponse", name, t, _include_actors(t))
        for name, t in (
            ("patient", "Patient"),
            ("practitioner", "Practitioner"),
            ("location", "Location"),
        )
    )

    return SearchRegistry(
        resource_type="AppointmentResponse",
        params={p.name: p for p in params},
        # Σ elements in the R4 AppointmentResponse definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "appointment",
                "participantType",
                "actor",
                "participantStatus",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"appointment", "participantStatus"}),
        # One include per target type, so `_include=AppointmentResponse:actor` brings in all
        # of them and `AppointmentResponse:actor:Location` just the Locations. RelatedPerson /
        # Device are not rebuilt resources here.
        includes=(
            *actor_includes,
            *narrowed_includes,
            IncludeTarget(
                "AppointmentResponse",
                "appointment",
                "Appointment",
                _include_appointment,
            ),
        ),
        # Nothing that references an AppointmentResponse is on the engine.
        revincludes=(),
        default_sort=lambda: [R.appointment_response_id.desc()],
    )
