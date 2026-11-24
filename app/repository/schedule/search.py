"""
FHIR R4 Schedule search parameters
(https://www.hl7.org/fhir/R4/schedule.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
schedule_search() below. Same arrangement as
app.repository.practitioner_role.search.

Each parameter's SQL reads only the search index (ScheduleModel's columns and
child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import exists, false, func, literal, or_, select, true

from app.repository._search_targets import MODELED
from app.fhir.search import (
    IncludeTarget,
    MultiValueSort,
    SearchError,
    SearchParam,
    SearchRegistry,
)
from app.fhir.search.sql import (
    coded_token_match,
    date_match,
    period_match,
    reference_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.models.schedule import (
    ScheduleActor,
    ScheduleIdentifier,
    ScheduleModel,
    ScheduleToken,
)

from ._shared import ACTOR_TYPES

S = ScheduleModel
_I = ScheduleIdentifier
_Tk = ScheduleToken
_A = ScheduleActor

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
    """Correlated EXISTS against one of the index child tables."""
    return exists(select(literal(1)).where(model.schedule_pk == S.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.schedule_pk == S.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(S.updated_at, S.created_at)


# ── _id / active / date ──────────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return S.schedule_id == int(token.code)


def _active_match(value, modifier, ctx):
    token = parse_token(value)
    if token.code not in ("true", "false") or token.system:  # boolean: no code system
        raise SearchError(value, f"'active' takes true or false, not '{value}'.")
    return S.active.is_(token.code == "true")


def _date_match(value, modifier, ctx):
    # Schedule.planningHorizon is a Period: matched as a range (see period_match).
    return period_match(S.planning_horizon_start, S.planning_horizon_end, value)


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


# ── the three CodeableConcept token parameters ───────────────────────────────


def _token_param(param: str):
    """(match, present, sort) for one of the token parameters held in the
    shared token table, selected by its `param` value."""

    def match(value, modifier, ctx):
        return _exists(
            _Tk,
            _Tk.param == param,
            coded_token_match(
                _Tk.system, _Tk.code, value, modifier, (_Tk.text_norm, _Tk.display_norm)
            ),
        )

    def present(ctx):
        return _exists(_Tk, _Tk.param == param)

    def sort():
        return _child_sort(_Tk.code, _Tk, _Tk.param == param)

    return match, present, sort


# ── actor (1..*, seven possible target types) ────────────────────────────────


def _actor_match(value, modifier, ctx):
    if modifier == "identifier":
        return _exists(
            _A,
            token_condition(
                _A.reference_identifier_system,
                _A.reference_identifier_value,
                parse_token(value),
            ),
        )
    # `modifier` is a target type (actor:Practitioner=30001) or None; a bare id
    # with no type is ambiguous across seven types and is rejected by
    # reference_target(). reference_type is a plain string here.
    return _exists(
        _A,
        reference_match(
            _A.reference_type,
            _A.reference_id,
            _A.reference_reference,
            value,
            modifier,
            ctx,
            ACTOR_TYPES,
            str,
        ),
    )


def _actor_present(ctx):
    return _exists(
        _A,
        or_(
            _A.reference_reference.is_not(None),
            _A.reference_identifier_value.is_not(None),
        ),
    )


def _actor_chain(target, inner, ctx):
    """`actor:<Type>.<param>=v`: some actor of that type (same tenant) matches
    `<param>=v`. The subquery doesn't correlate to the outer row — it ranges
    over the referenced resource."""
    model, id_col = _model(target)
    referenced = (
        select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)
    )
    return _exists(_A, _A.reference_type == target, _A.reference_id.in_(referenced))


# ── _include ─────────────────────────────────────────────────────────────────


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


def _include_actors(resource_type: str):
    """_include=Schedule:actor[:Type] — the actors of one type these
    schedules point at (only types that are resources on this server)."""

    async def fetch(session, ctx, schedules):
        model, id_col = _model(resource_type)
        referenced = select(_A.reference_id).where(
            _A.schedule_pk.in_({s.id for s in schedules}),
            _A.reference_type == resource_type,
            _A.reference_id.is_not(None),
        )
        return await _fetch(
            session,
            select(model).where(
                model.tenant_id == ctx.tenant_id, id_col.in_(referenced)
            ),
        )

    return fetch


async def _revinclude_slots(session, ctx, schedules):
    """_revinclude=Slot:schedule — the slots that belong to these schedules."""
    from app.models.slot import SlotModel

    ids = {s.schedule_id for s in schedules}
    stmt = select(SlotModel).where(
        SlotModel.tenant_id == ctx.tenant_id, SlotModel.schedule_id.in_(ids)
    )
    return list((await session.execute(stmt)).scalars().all())


def _register_kind() -> None:
    """How the search engine identifies and renders Schedule rows — for
    Schedule searches and for Schedules included by others."""
    from app.fhir.mappers.schedule import to_fhir_schedule
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind("Schedule", lambda s: s.schedule_id, to_fhir_schedule, "schedules")
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})


@cache
def schedule_search() -> SearchRegistry:
    _register_kind()

    def token(name, description, expression, example):
        match, present, sort = _token_param(name)
        return SearchParam(
            name,
            "token",
            description,
            expression,
            match,
            present,
            _TOKEN,
            sort=sort,
            example=example,
        )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public schedule id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: S.schedule_id,
            example="200001",
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
            "active",
            "token",
            "Is the schedule in active use",
            "Schedule.active",
            _active_match,
            lambda ctx: S.active.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: S.active,
            example="true",
            modifier_docs={
                "not": "`:not` — active is not this value, or is not recorded at all."
            },
        ),
        SearchParam(
            "actor",
            "reference",
            "The individual(HealthcareService, Practitioner, Location, ...) to find a Schedule for",
            "Schedule.actor",
            _actor_match,
            _actor_present,
            frozenset({"identifier", "missing"}),
            targets=ACTOR_TYPES,
            chain=_actor_chain,
            chain_targets={t: _registry_of(t) for t in ACTOR_TYPES if t in _MODELED},
            sort=lambda: _child_sort(_A.reference_id, _A),
            example="Practitioner/30001",
            modifier_docs={
                "identifier": "`:identifier` — match the logical identifier of an actor that has no resource here.",
            },
        ),
        SearchParam(
            "date",
            "date",
            "Search for Schedule resources that have a period that contains this date specified",
            "Schedule.planningHorizon",
            _date_match,
            lambda ctx: or_(
                S.planning_horizon_start.is_not(None),
                S.planning_horizon_end.is_not(None),
            ),
            sort=lambda: S.planning_horizon_start,
            example="ge2026-01-01",
        ),
        SearchParam(
            "identifier",
            "token",
            "A Schedule Identifier",
            "Schedule.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:schedules|S-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        token(
            "service-category",
            "High-level category",
            "Schedule.serviceCategory",
            "http://terminology.hl7.org/CodeSystem/service-category|17",
        ),
        token(
            "service-type",
            "The type of appointments that can be booked into associated slot(s)",
            "Schedule.serviceType",
            "http://terminology.hl7.org/CodeSystem/service-type|124",
        ),
        token(
            "specialty",
            "Type of specialty needed",
            "Schedule.specialty",
            "http://snomed.info/sct|394579002",
        ),
    ]

    return SearchRegistry(
        resource_type="Schedule",
        params={p.name: p for p in params},
        # Σ elements in the R4 Schedule definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "active",
                "serviceCategory",
                "serviceType",
                "specialty",
                "actor",
                "planningHorizon",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"actor"}),
        # One include per target type, so `_include=Schedule:actor` brings in all
        # of them and `Schedule:actor:Location` just the Locations. Patient /
        # RelatedPerson / Device aren't resources on this server.
        includes=tuple(
            IncludeTarget("Schedule", "actor", t, _include_actors(t))
            for t in ACTOR_TYPES
            if t in _MODELED
        ),
        # Slot is on the engine; Appointment (via its slots) will add its own later.
        revincludes=(
            IncludeTarget(
                "Slot", "schedule", "Schedule", _revinclude_slots, reverse=True
            ),
        ),
        default_sort=lambda: [S.schedule_id.desc()],
    )
