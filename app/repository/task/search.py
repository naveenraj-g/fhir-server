"""
FHIR R4 Task search parameters (https://www.hl7.org/fhir/R4/task.html#search) plus the common
`_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from task_search() below. Same
arrangement as app.repository.goal.search and app.repository.observation.search (references held
as columns, a shared token table and a shared reference table, Reference(Any) elements).

Each parameter's SQL reads only the search index (TaskModel's columns and child tables, see its
docstring) - never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
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
from app.models.task import (
    BASED_ON_TYPES,
    ENCOUNTER_TYPES,
    FOCUS_TYPES,
    FOR_TYPES,
    OWNER_TYPES,
    PART_OF_TYPES,
    REQUESTER_TYPES,
    TaskIdentifier,
    TaskIntent,
    TaskModel,
    TaskPriority,
    TaskReference,
    TaskStatus,
    TaskToken,
)
from app.repository._care_plan_revinclude import activity_care_plan_revincludes
from app.repository._search_targets import MODELED

P = TaskModel
_I = TaskIdentifier
_Tk = TaskToken
_R = TaskReference
_STATUS_SYSTEM = "http://hl7.org/fhir/task-status"
_INTENT_SYSTEM = "http://hl7.org/fhir/task-intent"
_PRIORITY_SYSTEM = "http://hl7.org/fhir/request-priority"

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
    return exists(select(literal(1)).where(model.task_pk == P.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.task_pk == P.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(P.updated_at, P.created_at)


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition. Does not correlate to
    the outer row - it ranges over the referenced resource."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return P.task_id == int(token.code)


def _enum_param(column, enum_cls, system: str):
    """(match, present) for a `code` bound to `system` and held in an enum column: `code` or
    `system|code`; another system or `|code` (no system) never matches; an unknown code matches
    nothing (rather than failing the Postgres enum cast)."""

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

    return match, lambda ctx: column.is_not(None)


# -- dates ---------------------------------------------------------------------------------


def _range_param(start, end):
    """(match, present) for a date search over a half-open range held in two columns."""

    def match(value, modifier, ctx):
        return period_match(start, end, value)

    return match, lambda ctx: or_(start.is_not(None), end.is_not(None))


# -- identifier / group-identifier / the token parameters ----------------------------------


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


def _group_identifier_match(value, modifier, ctx):
    return token_match(P.group_identifier_system, P.group_identifier_value, value)


def _token_param(param: str):
    """(match, present, sort) for one of the token parameters held in the shared token table,
    selected by its `param` value."""

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


# -- references held as columns: for (subject / patient), focus, encounter, requester, owner --


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    task row. `narrowed` restricts a multi-target element to one type (`patient` is `for`
    resolved to a Patient)."""
    ref, type_, id_ = (
        getattr(P, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(P, f"{prefix}_identifier_system"),
        getattr(P, f"{prefix}_identifier_value"),
    )
    # `is_not(None)` keeps `NOT present` (`:missing=true`) from going NULL for a row whose
    # reference has no resolved type (a logical, identifier-only reference).
    type_filter = (type_.is_not(None), type_ == narrowed) if narrowed else ()

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return and_(
                token_condition(ident_system, ident_value, parse_token(value)),
                *type_filter,
            )
        # `modifier` is a target type (subject:Patient=10001) or None; a bare id with several
        # targets is ambiguous and is rejected by reference_target().
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return and_(or_(ref.is_not(None), ident_value.is_not(None)), *type_filter)

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# -- based-on / part-of: the shared reference table ----------------------------------------


def _reference_param(param: str, targets: tuple[str, ...]):
    """(match, present, chain, sort) for one of the reference parameters held in the shared
    reference table, selected by its `param` value."""

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return _exists(
                _R,
                _R.param == param,
                token_condition(
                    _R.reference_identifier_system,
                    _R.reference_identifier_value,
                    parse_token(value),
                ),
            )
        return _exists(
            _R,
            _R.param == param,
            reference_match(
                _R.reference_type,
                _R.reference_id,
                _R.reference_reference,
                value,
                modifier,
                ctx,
                targets,
                str,
            ),
        )

    def present(ctx):
        return _exists(
            _R,
            _R.param == param,
            or_(
                _R.reference_reference.is_not(None),
                _R.reference_identifier_value.is_not(None),
            ),
        )

    def chain(target, inner, ctx):
        return _exists(
            _R,
            _R.param == param,
            _R.reference_type == target,
            _R.reference_id.in_(_referenced(target, inner, ctx)),
        )

    def sort():
        return _child_sort(_R.reference_id, _R, _R.param == param)

    return match, present, chain, sort


# -- _include / _revinclude ----------------------------------------------------------------


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


async def _load(session, ctx, resource_type: str, ids) -> list:
    if not ids:
        return []
    model, id_col = _model(resource_type)
    return await _fetch(
        session, select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids))
    )


def _include_column(prefix: str, resource_type: str):
    """_include of a reference held as columns (`for`, `focus`, `encounter`, `requester`,
    `owner`): the rows of `resource_type` these tasks point at."""

    async def fetch(session, ctx, tasks):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(t, id_)
            for t in tasks
            if getattr(t, type_) == resource_type and getattr(t, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_child(model, resource_type: str, *conditions):
    """_include of a reference held in the reference table (`based-on`, `part-of`)."""

    async def fetch(session, ctx, tasks):
        ids = select(model.reference_id).where(
            model.task_pk.in_({t.id for t in tasks}),
            model.reference_type == resource_type,
            model.reference_id.is_not(None),
            *conditions,
        )
        return await _load(
            session,
            ctx,
            resource_type,
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


def revinclude_tasks_via_column(prefix: str, resource_type: str, key):
    """_revinclude=Task:subject / :patient / :encounter / :owner / :requester - tasks whose column
    reference points at one of these rows (matched on the public id `key(row)`). Declared on the
    registry of each target type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        type_, id_ = getattr(P, f"{prefix}_type"), getattr(P, f"{prefix}_id")
        return await _fetch(
            session,
            select(P).where(
                P.tenant_id == ctx.tenant_id, type_ == resource_type, id_.in_(ids)
            ),
        )

    return fetch


def revinclude_tasks_via_reference(param: str, resource_type: str, key):
    """_revinclude=Task:part-of / :based-on - tasks with a row of `param` in the reference table
    pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.task_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(P).where(P.tenant_id == ctx.tenant_id, P.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Task rows."""
    from app.fhir.mappers.task import to_fhir_task
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(ResourceKind("Task", lambda t: t.task_id, to_fhir_task, "tasks"))


# -- registry ------------------------------------------------------------------------------

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def task_search() -> SearchRegistry:
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

    def enum_token(name, description, expression, column, enum_cls, system, example):
        match, present = _enum_param(column, enum_cls, system)
        return SearchParam(
            name,
            "token",
            description,
            expression,
            match,
            present,
            frozenset({"not", "missing"}),
            sort=lambda: column,
            example=example,
        )

    def date_param(name, description, expression, start, end, example):
        match, present = _range_param(start, end)
        return SearchParam(
            name,
            "date",
            description,
            expression,
            match,
            present,
            sort=lambda: start,
            example=example,
        )

    def column_ref(
        name, description, expression, prefix, targets, example, narrowed=None
    ):
        match, present, chain, sort = _column_ref(prefix, targets, narrowed)
        # A Reference(Any) chains through every rebuilt type; a known one through the types of
        # its own list that are rebuilt.
        reachable = [t for t in targets if t in _MODELED]
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
            chain_targets={t: _registry_of(t) for t in reachable},
            sort=sort,
            example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    def table_ref(name, description, expression, targets, example):
        match, present, chain, sort = _reference_param(name, targets)
        reachable = [t for t in targets if t in _MODELED]
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
            chain_targets={t: _registry_of(t) for t in reachable},
            sort=sort,
            example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    status_match, status_present = _enum_param(P.status, TaskStatus, _STATUS_SYSTEM)
    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public task id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.task_id,
            example="280001",
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
        date_param(
            "authored-on",
            "Search by creation date",
            "Task.authoredOn",
            P.authored_start,
            P.authored_end,
            "ge2026-01-01",
        ),
        table_ref(
            "based-on",
            "Search by requests this task is based on (Reference(Any))",
            "Task.basedOn",
            BASED_ON_TYPES,
            "ServiceRequest/80001",
        ),
        token(
            "business-status",
            "Search by business status",
            "Task.businessStatus",
            "http://example.org/business-status|waiting",
        ),
        token(
            "code",
            "Search by task code",
            "Task.code",
            "http://hl7.org/fhir/CodeSystem/task-code|fulfill",
        ),
        column_ref(
            "encounter",
            "Search by encounter",
            "Task.encounter",
            "encounter",
            ENCOUNTER_TYPES,
            "Encounter/20001",
        ),
        column_ref(
            "focus",
            "Search by task focus (Reference(Any))",
            "Task.focus",
            "focus",
            FOCUS_TYPES,
            "ServiceRequest/80001",
        ),
        SearchParam(
            "group-identifier",
            "token",
            "Search by group identifier",
            "Task.groupIdentifier",
            _group_identifier_match,
            lambda ctx: P.group_identifier_value.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.group_identifier_value,
            example="urn:groups|GRP-1",
        ),
        SearchParam(
            "identifier",
            "token",
            "Search for a task instance by its business identifier",
            "Task.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:tasks|T-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        enum_token(
            "intent",
            f"unknown | proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option (system {_INTENT_SYSTEM})",
            "Task.intent",
            P.intent,
            TaskIntent,
            _INTENT_SYSTEM,
            "order",
        ),
        date_param(
            "modified",
            "Search by last modification date",
            "Task.lastModified",
            P.modified_start,
            P.modified_end,
            "ge2026-01-01",
        ),
        column_ref(
            "owner",
            "Search by task owner",
            "Task.owner",
            "owner",
            OWNER_TYPES,
            "Practitioner/30001",
        ),
        table_ref(
            "part-of",
            "Search by task this task is part of",
            "Task.partOf",
            PART_OF_TYPES,
            "Task/280001",
        ),
        column_ref(
            "patient",
            "Search by patient",
            "Task.for.where(resolve() is Patient)",
            "for",
            ("Patient",),
            "10001",
            narrowed="Patient",
        ),
        token(
            "performer",
            "Search by recommended type of performer (e.g., Requester, Performer, Scheduler)",
            "Task.performerType",
            "http://terminology.hl7.org/CodeSystem/task-performer-type|requester",
        ),
        date_param(
            "period",
            "Search by period Task is/was underway",
            "Task.executionPeriod",
            P.period_start,
            P.period_end,
            "ge2026-01-01",
        ),
        enum_token(
            "priority",
            f"routine | urgent | asap | stat (system {_PRIORITY_SYSTEM})",
            "Task.priority",
            P.priority,
            TaskPriority,
            _PRIORITY_SYSTEM,
            "routine",
        ),
        column_ref(
            "requester",
            "Search by task requester",
            "Task.requester",
            "requester",
            REQUESTER_TYPES,
            "Practitioner/30001",
        ),
        SearchParam(
            "status",
            "token",
            f"draft | requested | received | accepted | rejected | ready | cancelled | in-progress | on-hold | failed | completed | entered-in-error (system {_STATUS_SYSTEM})",
            "Task.status",
            status_match,
            status_present,
            frozenset({"not", "missing"}),
            sort=lambda: P.status,
            example="requested",
        ),
        column_ref(
            "subject",
            "Search by subject (Reference(Any))",
            "Task.for",
            "for",
            FOR_TYPES,
            "Patient/10001",
        ),
    ]

    # Reference(Any) elements are followed to every rebuilt resource; a known reference to the
    # rebuilt types of its own list.
    def column_includes(param, prefix, targets):
        return tuple(
            IncludeTarget("Task", param, t, _include_column(prefix, t))
            for t in targets
            if t in _MODELED
        )

    def table_includes(param, targets):
        return tuple(
            IncludeTarget("Task", param, t, _include_child(_R, t, _R.param == param))
            for t in targets
            if t in _MODELED
        )

    includes = (
        IncludeTarget("Task", "patient", "Patient", _include_column("for", "Patient")),
        *column_includes("subject", "for", FOR_TYPES),
        *column_includes("focus", "focus", FOCUS_TYPES),
        *column_includes("encounter", "encounter", ENCOUNTER_TYPES),
        *column_includes("owner", "owner", OWNER_TYPES),
        *column_includes("requester", "requester", REQUESTER_TYPES),
        *table_includes("based-on", BASED_ON_TYPES),
        *table_includes("part-of", PART_OF_TYPES),
    )

    return SearchRegistry(
        resource_type="Task",
        params={p.name: p for p in params},
        # Σ elements in the R4 Task definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "instantiatesCanonical",
                "instantiatesUri",
                "basedOn",
                "groupIdentifier",
                "partOf",
                "status",
                "statusReason",
                "businessStatus",
                "intent",
                "code",
                "description",
                "focus",
                "for",
                "encounter",
                "executionPeriod",
                "lastModified",
                "requester",
                "owner",
                "location",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "intent"}),
        includes=includes,
        # A Task can be part of another Task, and a CarePlan can name a Task as an activity.
        revincludes=(
            *activity_care_plan_revincludes("Task", lambda t: t.task_id),
            IncludeTarget(
                "Task",
                "part-of",
                "Task",
                revinclude_tasks_via_reference("part-of", "Task", lambda t: t.task_id),
                reverse=True,
            ),
        ),
        default_sort=lambda: [P.task_id.desc()],
    )
