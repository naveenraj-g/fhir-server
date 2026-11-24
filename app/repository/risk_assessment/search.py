"""
FHIR R4 RiskAssessment search parameters
(https://www.hl7.org/fhir/R4/riskassessment.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`, `_include` /
`_revinclude`, and the OpenAPI docs all come from risk_assessment_search() below. Same
arrangement as app.repository.diagnostic_report.search (references held as columns, one
shared token table); `probability` is the engine's first `number` search
(app.fhir.search.quantity.number_range_match).

Each parameter's SQL reads only the search index (RiskAssessmentModel's columns and child
tables, see its docstring) — never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.repository._search_targets import MODELED
from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.quantity import number_range_match
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
from app.repository._clinical_impression_revinclude import (
    reference_impression_revincludes,
)
from app.models.risk_assessment import (
    PERFORMER_TYPES,
    SUBJECT_TYPES,
    RiskAssessmentIdentifier,
    RiskAssessmentModel,
    RiskAssessmentPrediction,
    RiskAssessmentToken,
)

M = RiskAssessmentModel
_I = RiskAssessmentIdentifier
_Tk = RiskAssessmentToken
_Pd = RiskAssessmentPrediction

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
    return exists(
        select(literal(1)).where(model.risk_assessment_pk == M.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.risk_assessment_pk == M.id, *conditions)
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
    return M.risk_assessment_id == int(token.code)


def _date_match(value, modifier, ctx):
    # RiskAssessment.occurrence as dateTime: matched as the range it covers.
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


def _probability_match(value, modifier, ctx):
    return _exists(
        _Pd, number_range_match(_Pd.probability_low, _Pd.probability_high, value)
    )


# ── references held as columns: subject / patient / encounter / condition / performer ──


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on
    the risk_assessment row. `narrowed` restricts a multi-target element to one type
    (`patient` is `subject` resolved to a Patient)."""
    ref, type_, id_ = (
        getattr(M, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(M, f"{prefix}_identifier_system"),
        getattr(M, f"{prefix}_identifier_value"),
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
    """_include of a reference held as columns: the rows of `resource_type` these assessments
    point at."""

    async def fetch(session, ctx, assessments):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(r, id_)
            for r in assessments
            if getattr(r, type_) == resource_type and getattr(r, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def revinclude_assessments_via_column(prefix: str, resource_type: str, key):
    """_revinclude=RiskAssessment:subject / :patient / :encounter / :condition / :performer —
    assessments whose column reference points at one of these rows (matched on the public id
    `key(row)`). Declared on the registry of each target type."""

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
    """How the search engine identifies and renders RiskAssessment rows."""
    from app.fhir.mappers.risk_assessment import to_fhir_risk_assessment
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "RiskAssessment",
            lambda r: r.risk_assessment_id,
            to_fhir_risk_assessment,
            "risk-assessments",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def risk_assessment_search() -> SearchRegistry:
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

    def column_ref(
        name, description, expression, prefix, targets, example, narrowed=None
    ):
        match, present, chain, sort = _column_ref(prefix, targets, narrowed)
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
            "Logical id of the resource (the public risk assessment id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.risk_assessment_id,
            example="520001",
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
        column_ref(
            "condition",
            "Condition assessed",
            "RiskAssessment.condition",
            "condition",
            ("Condition",),
            "Condition/120001",
        ),
        SearchParam(
            "date",
            "date",
            "When was assessment made?",
            "(RiskAssessment.occurrence as dateTime)",
            _date_match,
            lambda ctx: M.date_start.is_not(None),
            sort=lambda: M.date_start,
            example="ge2026-01-01",
        ),
        column_ref(
            "encounter",
            "Where was assessment performed?",
            "RiskAssessment.encounter",
            "encounter",
            ("Encounter",),
            "Encounter/20001",
        ),
        SearchParam(
            "identifier",
            "token",
            "Unique identifier for the assessment",
            "RiskAssessment.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:assessments|RA-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        token(
            "method",
            "Evaluation mechanism",
            "RiskAssessment.method",
            "http://snomed.info/sct|225338004",
        ),
        column_ref(
            "patient",
            "Who/what does assessment apply to?",
            "RiskAssessment.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        column_ref(
            "performer",
            "Who did assessment?",
            "RiskAssessment.performer",
            "performer",
            PERFORMER_TYPES,
            "Practitioner/30001",
        ),
        SearchParam(
            "probability",
            "number",
            "Likelihood of specified outcome",
            "RiskAssessment.prediction.probability",
            _probability_match,
            lambda ctx: _exists(_Pd),
            frozenset({"missing"}),
            sort=lambda: _child_sort(_Pd.probability_low, _Pd),
            example="gt0.5",
            modifier_docs={},
        ),
        token(
            "risk",
            "Likelihood of specified outcome as a qualitative value",
            "RiskAssessment.prediction.qualitativeRisk",
            "http://terminology.hl7.org/CodeSystem/risk-probability|moderate",
        ),
        column_ref(
            "subject",
            "Who/what does assessment apply to?",
            "RiskAssessment.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
    ]

    # One include per target type that is a resource here, so `_include=RiskAssessment:performer`
    # brings in all of them and `RiskAssessment:performer:Practitioner` just the Practitioners.
    performer_includes = tuple(
        IncludeTarget("RiskAssessment", "performer", t, _include_column("performer", t))
        for t in PERFORMER_TYPES
        if t in _MODELED
    )

    return SearchRegistry(
        resource_type="RiskAssessment",
        params={p.name: p for p in params},
        # Σ elements in the R4 RiskAssessment definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "status",
                "method",
                "code",
                "subject",
                "encounter",
                "occurrenceDateTime",
                "occurrencePeriod",
                "condition",
                "performer",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "subject"}),
        includes=(
            IncludeTarget(
                "RiskAssessment",
                "patient",
                "Patient",
                _include_column("subject", "Patient"),
            ),
            IncludeTarget(
                "RiskAssessment",
                "subject",
                "Patient",
                _include_column("subject", "Patient"),
            ),
            IncludeTarget(
                "RiskAssessment",
                "encounter",
                "Encounter",
                _include_column("encounter", "Encounter"),
            ),
            IncludeTarget(
                "RiskAssessment",
                "condition",
                "Condition",
                _include_column("condition", "Condition"),
            ),
            *performer_includes,
        ),
        # ClinicalImpression.investigation points here.
        revincludes=(
            *reference_impression_revincludes(
                "investigation", "RiskAssessment", lambda r: r.risk_assessment_id
            ),
        ),
        default_sort=lambda: [M.risk_assessment_id.desc()],
    )
