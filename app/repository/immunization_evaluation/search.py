"""
FHIR R4 ImmunizationEvaluation search parameters
(https://www.hl7.org/fhir/R4/immunizationevaluation.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`, `_include` /
`_revinclude`, and the OpenAPI docs all come from immunization_evaluation_search() below.
Same arrangement as app.repository.immunization.search (references held as columns,
shared token table).

Each parameter's SQL reads only the search index (ImmunizationEvaluationModel's columns
and child tables, see its docstring) — never `content`.
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
from app.repository._immunization_recommendation_revinclude import (
    support_recommendation_revincludes,
)
from app.models.immunization_evaluation import (
    ImmunizationEvaluationIdentifier,
    ImmunizationEvaluationModel,
    ImmunizationEvaluationStatus,
    ImmunizationEvaluationToken,
)

M = ImmunizationEvaluationModel
_I = ImmunizationEvaluationIdentifier
_Tk = ImmunizationEvaluationToken
# ImmunizationEvaluation.status is a `code` from the event-status code system.
_STATUS_SYSTEM = "http://hl7.org/fhir/event-status"

# Reference targets that are searchable resources on this server: the model to
# join for chaining / `_include`, and its registry.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = {
    "Patient": (
        "app.models.patient",
        "PatientModel",
        "patient_id",
        "app.repository.patient.search",
        "patient_search",
    ),
    "Immunization": (
        "app.models.immunization",
        "ImmunizationModel",
        "immunization_id",
        "app.repository.immunization.search",
        "immunization_search",
    ),
}


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
    return exists(
        select(literal(1)).where(model.immunization_evaluation_pk == M.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.immunization_evaluation_pk == M.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(M.updated_at, M.created_at)


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition. Does
    not correlate to the outer row — it ranges over the referenced resource."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return M.immunization_evaluation_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the event-status system: `code` or `system|code`;
    another system or `|code` (no system) never matches; an unknown code matches nothing
    (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == ImmunizationEvaluationStatus(token.code)
    except ValueError:
        return false()


def _date_match(value, modifier, ctx):
    # ImmunizationEvaluation.date is a dateTime: matched as the range it covers.
    return period_match(M.date_start, M.date_end, value)


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


def _column_ref(prefix: str, target: str):
    """(match, present, chain, sort) for a 1..1 Reference held as `{prefix}_*` columns on
    the immunization_evaluation row (single target, so a bare id works)."""
    ref, type_, id_ = (
        getattr(M, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(M, f"{prefix}_identifier_system"),
        getattr(M, f"{prefix}_identifier_value"),
    )

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return token_condition(ident_system, ident_value, parse_token(value))
        return reference_match(type_, id_, ref, value, modifier, ctx, (target,), str)

    def present(ctx):
        return or_(ref.is_not(None), ident_value.is_not(None))

    def chain(chain_target, inner, ctx):
        return and_(
            type_ == chain_target, id_.in_(_referenced(chain_target, inner, ctx))
        )

    return match, present, chain, lambda: id_


# ── _include / _revinclude ───────────────────────────────────────────────────


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
    """_include of a reference held as columns (`patient`, `immunization-event`): the
    rows of `resource_type` these evaluations point at."""

    async def fetch(session, ctx, evaluations):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(r, id_)
            for r in evaluations
            if getattr(r, type_) == resource_type and getattr(r, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def revinclude_evaluations_via_column(prefix: str, resource_type: str, key):
    """_revinclude=ImmunizationEvaluation:patient / :immunization-event — evaluations whose
    column reference points at one of these rows (matched on the public id `key(row)`).
    Declared on the registry of each target type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        type_, id_ = getattr(M, f"{prefix}_type"), getattr(M, f"{prefix}_id")
        return await _fetch(
            session,
            select(M).where(
                M.tenant_id == ctx.tenant_id, type_ == resource_type, id_.in_(ids)
            ),
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders ImmunizationEvaluation rows."""
    from app.fhir.mappers.immunization_evaluation import to_fhir_immunization_evaluation
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "ImmunizationEvaluation",
            lambda r: r.immunization_evaluation_id,
            to_fhir_immunization_evaluation,
            "immunization-evaluations",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def immunization_evaluation_search() -> SearchRegistry:
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

    def column_ref(name, description, expression, prefix, target, example):
        match, present, chain, sort = _column_ref(prefix, target)
        return SearchParam(
            name,
            "reference",
            description,
            expression,
            match,
            present,
            _REFERENCE,
            targets=(target,),
            chain=chain,
            chain_targets={target: _registry_of(target)},
            sort=sort,
            example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public immunization evaluation id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.immunization_evaluation_id,
            example="610001",
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
            "date",
            "date",
            "Date the evaluation was generated",
            "ImmunizationEvaluation.date",
            _date_match,
            lambda ctx: M.date_start.is_not(None),
            sort=lambda: M.date_start,
            example="ge2026-01-01",
        ),
        token(
            "dose-status",
            "The status of the dose relative to published recommendations",
            "ImmunizationEvaluation.doseStatus",
            "http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status|valid",
        ),
        SearchParam(
            "identifier",
            "token",
            "ID of the evaluation",
            "ImmunizationEvaluation.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:evaluations|IE-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        column_ref(
            "immunization-event",
            "The vaccine administration event being evaluated",
            "ImmunizationEvaluation.immunizationEvent",
            "immunization_event",
            "Immunization",
            "Immunization/330001",
        ),
        column_ref(
            "patient",
            "The patient being evaluated",
            "ImmunizationEvaluation.patient",
            "patient",
            "Patient",
            "Patient/10001",
        ),
        SearchParam(
            "status",
            "token",
            f"completed | entered-in-error (system {_STATUS_SYSTEM})",
            "ImmunizationEvaluation.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="completed",
        ),
        token(
            "target-disease",
            "The vaccine preventable disease being evaluated against",
            "ImmunizationEvaluation.targetDisease",
            "http://snomed.info/sct|40468003",
        ),
    ]

    return SearchRegistry(
        resource_type="ImmunizationEvaluation",
        params={p.name: p for p in params},
        # Σ elements in the R4 ImmunizationEvaluation definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {"status", "patient", "targetDisease", "immunizationEvent", "doseStatus"}
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset(
            {"status", "patient", "targetDisease", "immunizationEvent", "doseStatus"}
        ),
        includes=(
            IncludeTarget(
                "ImmunizationEvaluation",
                "patient",
                "Patient",
                _include_column("patient", "Patient"),
            ),
            IncludeTarget(
                "ImmunizationEvaluation",
                "immunization-event",
                "Immunization",
                _include_column("immunization_event", "Immunization"),
            ),
        ),
        # ImmunizationRecommendation.recommendation.supportingImmunization points here.
        revincludes=(
            *support_recommendation_revincludes(
                "ImmunizationEvaluation", lambda r: r.immunization_evaluation_id
            ),
        ),
        default_sort=lambda: [M.immunization_evaluation_id.desc()],
    )
