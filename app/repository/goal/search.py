"""
FHIR R4 Goal search parameters (https://www.hl7.org/fhir/R4/goal.html#search) plus the common
`_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from goal_search() below. Same
arrangement as app.repository.care_plan.search (a multi-target subject held as columns, `patient`
narrowed to Patients, shared token table).

Each parameter's SQL reads only the search index (GoalModel's columns and child tables, see its
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
from app.models.goal import (
    SUBJECT_TYPES,
    GoalIdentifier,
    GoalLifecycleStatus,
    GoalModel,
    GoalTarget,
    GoalToken,
)
from app.repository._care_plan_revinclude import reference_care_plan_revincludes
from app.repository._search_targets import MODELED

P = GoalModel
_I = GoalIdentifier
_Tk = GoalToken
_T = GoalTarget
_STATUS_SYSTEM = "http://hl7.org/fhir/goal-status"

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
    return exists(select(literal(1)).where(model.goal_pk == P.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.goal_pk == P.id, *conditions)
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
    return P.goal_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`lifecycle-status` is a `code` bound to the goal-status system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an unknown code matches
    nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return P.lifecycle_status.is_not(None)
    try:
        return P.lifecycle_status == GoalLifecycleStatus(token.code)
    except ValueError:
        return false()


def _start_date_match(value, modifier, ctx):
    # Goal.start as a date: matched as the range it covers (a goal with a startCodeableConcept
    # or no start never matches).
    return period_match(P.start_start, P.start_end, value)


def _target_date_match(value, modifier, ctx):
    return _exists(_T, period_match(_T.due_start, _T.due_end, value))


# -- identifier / the token parameters -----------------------------------------------------


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


# -- subject / patient: a multi-target reference held as columns ---------------------------


def _subject_ref(targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for `subject` (or `patient`, `subject` narrowed to one
    type) held as `subject_*` columns on the goal row."""
    ref, type_, id_ = (P.subject_reference, P.subject_type, P.subject_id)
    ident_system, ident_value = P.subject_identifier_system, P.subject_identifier_value
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


def _include_subject(resource_type: str):
    """_include of `subject` / `patient`: the rows of `resource_type` these goals point at."""

    async def fetch(session, ctx, goals):
        ids = {
            g.subject_id
            for g in goals
            if g.subject_type == resource_type and g.subject_id
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def revinclude_goals_via_column(prefix: str, resource_type: str, key):
    """_revinclude=Goal:subject / :patient - goals whose `subject` points at one of these rows
    (matched on the public id `key(row)`). Declared on the registry of each target type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        return await _fetch(
            session,
            select(P).where(
                P.tenant_id == ctx.tenant_id,
                P.subject_type == resource_type,
                P.subject_id.in_(ids),
            ),
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Goal rows."""
    from app.fhir.mappers.goal import to_fhir_goal
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(ResourceKind("Goal", lambda g: g.goal_id, to_fhir_goal, "goals"))


# -- registry ------------------------------------------------------------------------------

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def goal_search() -> SearchRegistry:
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

    def subject_param(name, description, expression, narrowed, example):
        # `patient` is `subject` narrowed to Patient: one target, so a bare id works.
        targets = (narrowed,) if narrowed else SUBJECT_TYPES
        match, present, chain, sort = _subject_ref(targets, narrowed)
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
            sort=sort,
            example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public goal id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.goal_id,
            example="460001",
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
            "achievement-status",
            "in-progress | improving | worsening | no-change | achieved | sustaining | not-achieved | no-progress | not-attainable",
            "Goal.achievementStatus",
            "http://terminology.hl7.org/CodeSystem/goal-achievement|achieved",
        ),
        token(
            "category",
            "E.g. Treatment, dietary, behavioral, etc.",
            "Goal.category",
            "http://terminology.hl7.org/CodeSystem/goal-category|dietary",
        ),
        SearchParam(
            "identifier",
            "token",
            "External Ids for this goal",
            "Goal.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:goals|G-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "lifecycle-status",
            "token",
            f"proposed | planned | accepted | active | on-hold | completed | cancelled | entered-in-error | rejected (system {_STATUS_SYSTEM})",
            "Goal.lifecycleStatus",
            _status_match,
            lambda ctx: P.lifecycle_status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.lifecycle_status,
            example="active",
        ),
        subject_param(
            "patient",
            "Who this goal is intended for",
            "Goal.subject.where(resolve() is Patient)",
            "Patient",
            "10001",
        ),
        SearchParam(
            "start-date",
            "date",
            "When goal pursuit begins",
            "(Goal.start as date)",
            _start_date_match,
            lambda ctx: P.start_start.is_not(None),
            sort=lambda: P.start_start,
            example="ge2026-01-01",
        ),
        subject_param(
            "subject",
            "Who this goal is intended for",
            "Goal.subject",
            None,
            "Patient/10001",
        ),
        SearchParam(
            "target-date",
            "date",
            "Reach goal on or before",
            "(Goal.target.due as date)",
            _target_date_match,
            lambda ctx: _exists(_T, _T.due_start.is_not(None)),
            sort=lambda: _child_sort(_T.due_start, _T),
            example="le2026-12-31",
        ),
    ]

    modeled_subjects = [t for t in SUBJECT_TYPES if t in _MODELED]
    subject_includes = tuple(
        IncludeTarget("Goal", "subject", t, _include_subject(t))
        for t in modeled_subjects
    )

    return SearchRegistry(
        resource_type="Goal",
        params={p.name: p for p in params},
        # Σ elements in the R4 Goal definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "lifecycleStatus",
                "achievementStatus",
                "category",
                "priority",
                "description",
                "subject",
                "startDate",
                "startCodeableConcept",
                "target",
                "statusDate",
                "expressedBy",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"lifecycleStatus", "description", "subject"}),
        includes=(
            IncludeTarget("Goal", "patient", "Patient", _include_subject("Patient")),
            *subject_includes,
        ),
        # A CarePlan names its goals.
        revincludes=(
            *reference_care_plan_revincludes("goal", "Goal", lambda g: g.goal_id),
        ),
        default_sort=lambda: [P.goal_id.desc()],
    )
