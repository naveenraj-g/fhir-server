"""
FHIR R4 MeasureReport search parameters
(https://www.hl7.org/fhir/R4/measurereport.html#search) plus the common `_id` / `_lastUpdated`,
declared once for app.fhir.search: parsing, SQL, `_sort`, `_include` / `_revinclude`, chaining and
the OpenAPI docs all come from measure_report_search() below. Same arrangement as
app.repository.questionnaire_response.search (references held as columns, a shared reference
table, a canonical URL resolved against the target's own `url`).

R4 defines nine parameters: `status`, `identifier`, the dates `date` and `period`, the
references `subject` / `patient` / `reporter` (columns), `evaluated-resource` (Reference(Any),
the reference table) and `measure` (a canonical URL, the reference table, resolved against a
stored Measure's `url`).

Each parameter's SQL reads only the search index (MeasureReportModel's columns and child tables,
see its docstring) - never `content`.
"""

from __future__ import annotations

import importlib
import re
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    date_match,
    period_match,
    reference_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import like_escape, parse_of_type, parse_token
from app.models.measure_report import (
    REFERENCE_TYPES,
    REPORTER_TYPES,
    SUBJECT_TYPES,
    MeasureReportIdentifier,
    MeasureReportModel,
    MeasureReportReference,
    MeasureReportStatus,
)
from app.repository._search_targets import MODELED

M = MeasureReportModel
_I = MeasureReportIdentifier
_R = MeasureReportReference

# MeasureReport.status is a `code` from the R4 measure-report-status system.
_STATUS_SYSTEM = "http://hl7.org/fhir/measure-report-status"
_ABSOLUTE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")

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
        select(literal(1)).where(model.measure_report_pk == M.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.measure_report_pk == M.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(M.updated_at, M.created_at)


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
    return M.measure_report_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the measure-report-status system: `code` or `system|code`;
    another system or `|code` (no system) never matches; an unknown code matches nothing (rather
    than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == MeasureReportStatus(token.code)
    except ValueError:
        return false()


def _range_param(start, end):
    """(match, present) for a date search over a half-open range held in two columns."""

    def match(value, modifier, ctx):
        return period_match(start, end, value)

    return match, lambda ctx: or_(start.is_not(None), end.is_not(None))


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


# ── references held as columns: subject / patient, reporter ──────────────────────────────


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    measure_report row. `narrowed` restricts a multi-target element to one type (`patient` is
    `subject` resolved to a Patient)."""
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


# ── measure / evaluated-resource: one row per Reference in the shared table ──────────────


def _reference_param(param: str):
    """(match, present, chain, sort) for `evaluated-resource`, held in the shared reference
    table, selected by its `param` value."""
    targets = REFERENCE_TYPES[param]

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


def _canonical_matches(row_model, ref):
    """Condition: the measure reference `ref` (a reference-table row) resolves to the Measure
    row `row_model` - by a relative `Measure/<id>`, by an equal canonical URL or by `url|version`
    (the stored canonical starts with the Measure's own url + `|`)."""
    return or_(
        and_(
            ref.reference_type == "Measure",
            ref.reference_id == row_model.measure_id,
        ),
        and_(row_model.url.is_not(None), ref.reference_reference == row_model.url),
        and_(
            row_model.url.is_not(None),
            func.substr(ref.reference_reference, 1, func.length(row_model.url) + 1)
            == row_model.url.concat("|"),
        ),
    )


def _measure_chain(target, inner, ctx):
    """`measure.title=...`: a report whose canonical resolves to a Measure in the same tenant
    that matches `inner`. The canonical string is resolved against the Measure's own `url` (an
    unversioned or versioned canonical) or its public id."""
    model, _id = _model("Measure")
    return _exists(
        _R,
        _R.param == "measure",
        exists(
            select(literal(1))
            .where(
                model.tenant_id == ctx.tenant_id, _canonical_matches(model, _R), inner
            )
            .correlate(_R)
        ),
    )


def _measure_param():
    """`measure` searches the canonical URL of the Measure (optionally versioned, `url|1.0`). A
    search value matches a stored canonical equal to it; an unversioned absolute URL also
    matches the stored versions of that URL; a relative `Measure/<id>` matches by its resolved
    type and id."""
    param = "measure"
    targets = REFERENCE_TYPES[param]

    def match(value, modifier, ctx):
        conditions = [
            reference_match(
                _R.reference_type,
                _R.reference_id,
                _R.reference_reference,
                value,
                modifier,
                ctx,
                targets,
                str,
            )
        ]
        if modifier is None and "|" not in value and _ABSOLUTE.match(value):
            conditions.append(
                _R.reference_reference.like(like_escape(value) + "|%", escape="\\")
            )
        return _exists(_R, _R.param == param, or_(*conditions))

    def present(ctx):
        return _exists(_R, _R.param == param)

    def sort():
        return _child_sort(_R.reference_reference, _R, _R.param == param)

    return match, present, sort


# ── _include / _revinclude ───────────────────────────────────────────────────────────────


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
    """_include of a reference held as columns: the rows of `resource_type` these reports point
    at."""

    async def fetch(session, ctx, reports):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(r, id_)
            for r in reports
            if getattr(r, type_) == resource_type and getattr(r, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_reference(param: str, resource_type: str):
    """_include of a reference held in the shared reference table: the rows of `resource_type`
    these reports' `param` references point at."""

    async def fetch(session, ctx, reports):
        ids = select(_R.reference_id).where(
            _R.measure_report_pk.in_({r.id for r in reports}),
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.is_not(None),
        )
        return await _load(
            session,
            ctx,
            resource_type,
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


async def _include_measure(session, ctx, reports):
    """_include=MeasureReport:measure - the Measures these reports' canonical URLs (or relative
    `Measure/<id>` references) resolve to. An unversioned canonical brings in every stored
    version of that url."""
    model, _id = _model("Measure")
    rows = (
        await session.execute(
            select(_R.reference_reference, _R.reference_type, _R.reference_id).where(
                _R.measure_report_pk.in_({r.id for r in reports}),
                _R.param == "measure",
            )
        )
    ).all()
    urls, ids = set(), set()
    for reference, rtype, rid in rows:
        if rtype == "Measure" and rid:
            ids.add(rid)
        elif reference:
            urls.add(reference.split("|", 1)[0])
    conditions = []
    if ids:
        conditions.append(model.measure_id.in_(ids))
    if urls:
        conditions.append(model.url.in_(urls))
    if not conditions:
        return []
    return await _fetch(
        session, select(model).where(model.tenant_id == ctx.tenant_id, or_(*conditions))
    )


def revinclude_reports_via_measure(key_url, key_id):
    """_revinclude=MeasureReport:measure - the reports whose canonical resolves to one of these
    Measures (matched on url / `url|version` / the public id). Declared on the Measure registry."""

    async def fetch(session, ctx, rows):
        conditions = []
        for row in rows:
            url = key_url(row)
            conditions.append(
                and_(_R.reference_type == "Measure", _R.reference_id == key_id(row))
            )
            if url:
                conditions.append(_R.reference_reference == url)
                conditions.append(
                    _R.reference_reference.like(like_escape(url) + "|%", escape="\\")
                )
        if not conditions:
            return []
        pks = select(_R.measure_report_pk).where(
            _R.param == "measure", or_(*conditions)
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def revinclude_reports_via_column(prefix: str, resource_type: str, key):
    """_revinclude=MeasureReport:subject / :patient / :reporter - reports whose column reference
    points at one of these rows (matched on the public id `key(row)`). Declared on the registry
    of each target type."""

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


def revinclude_reports_via_reference(param: str, resource_type: str, key):
    """_revinclude=MeasureReport:evaluated-resource - reports with a reference row of `param`
    pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.measure_report_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders MeasureReport rows."""
    from app.fhir.mappers.measure_report import to_fhir_measure_report
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "MeasureReport",
            lambda r: r.measure_report_id,
            to_fhir_measure_report,
            "measure-reports",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────────────────

_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def measure_report_search() -> SearchRegistry:
    _register_kind()

    def column_ref(
        name, description, expression, prefix, targets, example, narrowed=None
    ):
        match, present, chain, sort = _column_ref(prefix, targets, narrowed)
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

    evaluated_match, evaluated_present, evaluated_chain, evaluated_sort = (
        _reference_param("evaluated-resource")
    )
    evaluated_targets = REFERENCE_TYPES["evaluated-resource"]
    measure_match, measure_present, measure_sort = _measure_param()
    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public measure report id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.measure_report_id,
            example="570001",
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
            "date",
            "The date of the measure report",
            "MeasureReport.date",
            M.date_start,
            M.date_end,
            "ge2026-01-01",
        ),
        SearchParam(
            "evaluated-resource",
            "reference",
            "An evaluated resource referenced by the measure report (Reference(Any))",
            "MeasureReport.evaluatedResource",
            evaluated_match,
            evaluated_present,
            _REFERENCE,
            targets=evaluated_targets,
            chain=evaluated_chain,
            chain_targets={
                t: _registry_of(t) for t in evaluated_targets if t in _MODELED
            },
            sort=evaluated_sort,
            example="Observation/160001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        SearchParam(
            "identifier",
            "token",
            "External identifier of the measure report to be returned",
            "MeasureReport.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:measure-reports|MR-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "measure",
            "reference",
            "The measure to return measure report results for (a canonical URL)",
            "MeasureReport.measure",
            measure_match,
            measure_present,
            frozenset({"missing"}),
            targets=REFERENCE_TYPES["measure"],
            chain=_measure_chain,
            chain_targets={"Measure": _registry_of("Measure")},
            sort=measure_sort,
            example="https://fhir-server.dev/fhir/Measure/readmission",
            modifier_docs={
                "missing": "`:missing=true` — reports with no measure; `:missing=false` — reports that name one."
            },
        ),
        column_ref(
            "patient",
            "The identity of a patient to search for individual measure report results for",
            "MeasureReport.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "10001",
            narrowed="Patient",
        ),
        date_param(
            "period",
            "The period of the measure report",
            "MeasureReport.period",
            M.period_start,
            M.period_end,
            "ge2026-01-01",
        ),
        column_ref(
            "reporter",
            "The reporter to return measure report results for",
            "MeasureReport.reporter",
            "reporter",
            REPORTER_TYPES,
            "Organization/190001",
        ),
        SearchParam(
            "status",
            "token",
            f"complete | pending | error (system {_STATUS_SYSTEM})",
            "MeasureReport.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="complete",
        ),
        column_ref(
            "subject",
            "The identity of a subject to search for individual measure report results for",
            "MeasureReport.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
    ]

    def column_includes(param, prefix, targets):
        return tuple(
            IncludeTarget("MeasureReport", param, t, _include_column(prefix, t))
            for t in targets
            if t in _MODELED
        )

    return SearchRegistry(
        resource_type="MeasureReport",
        params={p.name: p for p in params},
        # Σ elements in the R4 MeasureReport definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "status",
                "type",
                "measure",
                "subject",
                "date",
                "reporter",
                "period",
                "improvementNotation",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "type", "measure", "period"}),
        includes=(
            IncludeTarget(
                "MeasureReport",
                "patient",
                "Patient",
                _include_column("subject", "Patient"),
            ),
            *column_includes("subject", "subject", SUBJECT_TYPES),
            *column_includes("reporter", "reporter", REPORTER_TYPES),
            IncludeTarget("MeasureReport", "measure", "Measure", _include_measure),
            *(
                IncludeTarget(
                    "MeasureReport",
                    "evaluated-resource",
                    t,
                    _include_reference("evaluated-resource", t),
                )
                for t in evaluated_targets
                if t in _MODELED
            ),
        ),
        revincludes=(),
        default_sort=lambda: [M.measure_report_id.desc()],
    )
