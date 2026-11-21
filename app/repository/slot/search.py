"""
FHIR R4 Slot search parameters
(https://www.hl7.org/fhir/R4/slot.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include`, and the OpenAPI docs all come from slot_search() below. Same
arrangement as app.repository.schedule.search.

Each parameter's SQL reads only the search index (SlotModel's columns and
child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

from functools import cache

from sqlalchemy import exists, false, func, literal, or_, select, true

from app.repository._appointment_revinclude import slot_revincludes
from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    coded_token_match,
    date_match,
    reference_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.models.enums import ScheduleReferenceType
from app.models.slot import SlotIdentifier, SlotModel, SlotStatus, SlotToken

S = SlotModel
_I = SlotIdentifier
_Tk = SlotToken
_STATUS_SYSTEM = "http://hl7.org/fhir/slotstatus"


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(select(literal(1)).where(model.slot_pk == S.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.slot_pk == S.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(S.updated_at, S.created_at)


# ── _id / status / start ─────────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return S.slot_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to one code system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an
    unknown code matches nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return S.status.is_not(None)
    try:
        return S.status == SlotStatus(token.code)
    except ValueError:
        return false()


def _start_match(value, modifier, ctx):
    # Slot.start is an instant: matched as a point in time (see date_match).
    return date_match(S.start, value)


# ── identifier / the four CodeableConcept token parameters ───────────────────


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


# ── schedule (1..1 reference held on the row) ────────────────────────────────


def _schedule_match(value, modifier, ctx):
    if modifier == "identifier":
        return token_condition(
            S.schedule_identifier_system,
            S.schedule_identifier_value,
            parse_token(value),
        )
    return reference_match(
        S.schedule_type,
        S.schedule_id,
        S.schedule_reference,
        value,
        modifier,
        ctx,
        ("Schedule",),
        ScheduleReferenceType,
    )


def _schedule_present(ctx):
    return or_(
        S.schedule_reference.is_not(None), S.schedule_identifier_value.is_not(None)
    )


def _schedule_chain(target, inner, ctx):
    """`schedule.<param>=v`: the Schedule (same tenant) matches any Schedule
    search parameter (e.g. `schedule.actor:Practitioner.family=Careful`). The
    subquery doesn't correlate to the outer row — it ranges over the Schedule."""
    from app.models.schedule import ScheduleModel as Sched

    referenced = (
        select(Sched.schedule_id)
        .where(Sched.tenant_id == ctx.tenant_id, inner)
        .correlate(None)
    )
    return S.schedule_id.in_(referenced)


def _schedule_search():
    from app.repository.schedule.search import schedule_search

    return schedule_search()


# ── _include ─────────────────────────────────────────────────────────────────


async def _include_schedule(session, ctx, slots):
    """_include=Slot:schedule — the schedules these slots belong to."""
    from app.models.schedule import ScheduleModel as Sched

    ids = {s.schedule_id for s in slots if s.schedule_id is not None}
    if not ids:
        return []
    stmt = select(Sched).where(
        Sched.tenant_id == ctx.tenant_id, Sched.schedule_id.in_(ids)
    )
    return list((await session.execute(stmt)).scalars().all())


def _register_kind() -> None:
    """How the search engine identifies and renders Slot rows."""
    from app.fhir.mappers.slot import to_fhir_slot
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(ResourceKind("Slot", lambda s: s.slot_id, to_fhir_slot, "slots"))


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})


@cache
def slot_search() -> SearchRegistry:
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
            "Logical id of the resource (the public slot id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: S.slot_id,
            example="220001",
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
        token(
            "appointment-type",
            "The style of appointment or patient that may be booked in the slot (not service type)",
            "Slot.appointmentType",
            "http://terminology.hl7.org/CodeSystem/v2-0276|ROUTINE",
        ),
        SearchParam(
            "identifier",
            "token",
            "A Slot Identifier",
            "Slot.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:slots|SL-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "schedule",
            "reference",
            "The Schedule Resource that we are seeking a slot within",
            "Slot.schedule",
            _schedule_match,
            _schedule_present,
            frozenset({"identifier", "missing"}),
            targets=("Schedule",),
            chain=_schedule_chain,
            chain_targets={"Schedule": _schedule_search},
            sort=lambda: S.schedule_id,
            example="Schedule/200001",
        ),
        token(
            "service-category",
            "A broad categorization of the service that is to be performed during this appointment",
            "Slot.serviceCategory",
            "http://terminology.hl7.org/CodeSystem/service-category|17",
        ),
        token(
            "service-type",
            "The type of appointments that can be booked into the slot",
            "Slot.serviceType",
            "http://terminology.hl7.org/CodeSystem/service-type|124",
        ),
        token(
            "specialty",
            "The specialty of a practitioner that would be required to perform the service requested in this appointment",
            "Slot.specialty",
            "http://snomed.info/sct|394579002",
        ),
        SearchParam(
            "start",
            "date",
            "Appointment date/time.",
            "Slot.start",
            _start_match,
            lambda ctx: S.start.is_not(None),
            sort=lambda: S.start,
            example="ge2026-06-01T09:00:00Z",
        ),
        SearchParam(
            "status",
            "token",
            f"The free/busy status of the appointment (busy | free | busy-unavailable | busy-tentative | entered-in-error; system {_STATUS_SYSTEM})",
            "Slot.status",
            _status_match,
            lambda ctx: S.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: S.status,
            example="free",
        ),
    ]

    return SearchRegistry(
        resource_type="Slot",
        params={p.name: p for p in params},
        # Σ elements in the R4 Slot definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "serviceCategory",
                "serviceType",
                "specialty",
                "appointmentType",
                "schedule",
                "status",
                "start",
                "end",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"schedule", "status", "start", "end"}),
        includes=(IncludeTarget("Slot", "schedule", "Schedule", _include_schedule),),
        # Appointment.slot points here.
        revincludes=slot_revincludes(lambda s: s.slot_id),
        default_sort=lambda: [S.slot_id.desc()],
    )
