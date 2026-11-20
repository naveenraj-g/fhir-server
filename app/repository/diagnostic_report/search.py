"""
FHIR R4 DiagnosticReport search parameters
(https://www.hl7.org/fhir/R4/diagnosticreport.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
diagnostic_report_search() below. Same arrangement as
app.repository.procedure.search and app.repository.condition.search (references
held as columns, shared token / reference / performer tables).

Each parameter's SQL reads only the search index (DiagnosticReportModel's columns
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
from app.repository._procedure_revinclude import reason_procedure_revincludes
from app.models.diagnostic_report import (
    PERFORMER_TYPES,
    REFERENCE_TYPES,
    SUBJECT_TYPES,
    DiagnosticReportIdentifier,
    DiagnosticReportModel,
    DiagnosticReportPerformer,
    DiagnosticReportReference,
    DiagnosticReportStatus,
    DiagnosticReportToken,
)

D = DiagnosticReportModel
_I = DiagnosticReportIdentifier
_Tk = DiagnosticReportToken
_R = DiagnosticReportReference
_Pf = DiagnosticReportPerformer
_STATUS_SYSTEM = "http://hl7.org/fhir/diagnostic-report-status"

# Reference targets that are searchable resources on this server: the model to
# join for chaining / `_include`, and its registry.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = {
    "Patient": ("app.models.patient", "PatientModel", "patient_id",
                "app.repository.patient.search", "patient_search"),
    "Practitioner": ("app.models.practitioner", "PractitionerModel", "practitioner_id",
                     "app.repository.practitioner.search", "practitioner_search"),
    "PractitionerRole": ("app.models.practitioner_role", "PractitionerRoleModel", "practitioner_role_id",
                         "app.repository.practitioner_role.search", "practitioner_role_search"),
    "Organization": ("app.models.organization", "OrganizationModel", "organization_id",
                     "app.repository.organization.search", "organization_search"),
    "Encounter": ("app.models.encounter", "EncounterModel", "encounter_id",
                  "app.repository.encounter.search", "encounter_search"),
    "Location": ("app.models.location", "LocationModel", "location_id",
                 "app.repository.location.search", "location_search"),
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
    return exists(select(literal(1)).where(model.diagnostic_report_pk == D.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return select(fn(column)).where(model.diagnostic_report_pk == D.id, *conditions).scalar_subquery()

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(D.updated_at, D.created_at)


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition. Does
    not correlate to the outer row — it ranges over the referenced resource."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system or not (token.code or "").isdigit():  # ids are the numeric public id
        return false()
    return D.diagnostic_report_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the diagnostic-report-status system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an unknown
    code matches nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return D.status.is_not(None)
    try:
        return D.status == DiagnosticReportStatus(token.code)
    except ValueError:
        return false()


def _date_match(value, modifier, ctx):
    # DiagnosticReport.effective[x] as a dateTime or a Period: matched as a range.
    return period_match(D.effective_date_start, D.effective_date_end, value)


# ── identifier / the three token parameters ──────────────────────────────────


def _identifier_match(value, modifier, ctx):
    if modifier == "text":
        return _exists(_I, token_text_match((_I.type_text_norm, _I.type_display_norm), value))
    if modifier == "of-type":
        type_system, type_code, ident = parse_of_type(value)
        return _exists(_I, _I.type_system == type_system, _I.type_code == type_code, _I.value == ident)
    return _exists(_I, token_match(_I.system, _I.value, value))


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


# ── references held as columns: subject / patient / encounter ────────────────


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*`
    columns on the diagnostic_report row. `narrowed` restricts a multi-target
    element to one type (`patient` is `subject` resolved to a Patient)."""
    ref, type_, id_ = (getattr(D, f"{prefix}_{part}") for part in ("reference", "type", "id"))
    ident_system, ident_value = getattr(D, f"{prefix}_identifier_system"), getattr(D, f"{prefix}_identifier_value")
    # `is_not(None)` keeps `NOT present` (`:missing=true`) from going NULL for a row whose
    # reference has no resolved type (a logical, identifier-only reference).
    type_filter = (type_.is_not(None), type_ == narrowed) if narrowed else ()

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return and_(token_condition(ident_system, ident_value, parse_token(value)), *type_filter)
        # `modifier` is a target type (subject:Patient=10001) or None; a bare id
        # with several targets is ambiguous and is rejected by reference_target().
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return and_(or_(ref.is_not(None), ident_value.is_not(None)), *type_filter)

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# ── references held in the reference table: based-on / media / result / specimen ──


def _reference_param(param: str, targets: tuple[str, ...]):
    """(match, present, chain, sort) for one of the reference parameters held
    in the shared reference table, selected by its `param` value."""

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
            reference_match(
                _R.reference_type, _R.reference_id, _R.reference_reference, value, modifier, ctx, targets, str
            ),
        )

    def present(ctx):
        return _exists(
            _R, _R.param == param, or_(_R.reference_reference.is_not(None), _R.reference_identifier_value.is_not(None))
        )

    def sort():
        return _child_sort(_R.reference_id, _R, _R.param == param)

    return match, present, sort


# ── performer / results-interpreter ──────────────────────────────────────────


def _performer_param(param: str):
    """(match, present, chain, sort) for `performer` or `results-interpreter`,
    both held in the performer table and told apart by `param`."""

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return _exists(
                _Pf,
                _Pf.param == param,
                token_condition(_Pf.reference_identifier_system, _Pf.reference_identifier_value, parse_token(value)),
            )
        return _exists(
            _Pf,
            _Pf.param == param,
            reference_match(
                _Pf.reference_type, _Pf.reference_id, _Pf.reference_reference, value, modifier, ctx, PERFORMER_TYPES, str
            ),
        )

    def present(ctx):
        return _exists(
            _Pf, _Pf.param == param, or_(_Pf.reference_reference.is_not(None), _Pf.reference_identifier_value.is_not(None))
        )

    def chain(target, inner, ctx):
        return _exists(_Pf, _Pf.param == param, _Pf.reference_type == target, _Pf.reference_id.in_(_referenced(target, inner, ctx)))

    def sort():
        return _child_sort(_Pf.reference_id, _Pf, _Pf.param == param)

    return match, present, chain, sort


# ── _include / _revinclude ───────────────────────────────────────────────────


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


async def _load(session, ctx, resource_type: str, ids) -> list:
    if not ids:
        return []
    model, id_col = _model(resource_type)
    return await _fetch(session, select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids)))


def _include_column(prefix: str, resource_type: str):
    """_include of a reference held as columns (`subject`, `patient`,
    `encounter`): the rows of `resource_type` these reports point at."""

    async def fetch(session, ctx, reports):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {getattr(r, id_) for r in reports if getattr(r, type_) == resource_type and getattr(r, id_)}
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_performer(param: str, resource_type: str):
    """_include of `performer` / `results-interpreter`: the rows of `resource_type`."""

    async def fetch(session, ctx, reports):
        ids = select(_Pf.reference_id).where(
            _Pf.diagnostic_report_pk.in_({r.id for r in reports}),
            _Pf.param == param,
            _Pf.reference_type == resource_type,
            _Pf.reference_id.is_not(None),
        )
        return await _load(session, ctx, resource_type, set((await session.execute(ids)).scalars().all()))

    return fetch


def revinclude_reports_via_column(prefix: str, resource_type: str, key):
    """_revinclude=DiagnosticReport:subject / :patient / :encounter — reports whose
    column reference points at one of these rows (matched on the public id
    `key(row)`). Declared on the registry of each target type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        type_, id_ = getattr(D, f"{prefix}_type"), getattr(D, f"{prefix}_id")
        return await _fetch(session, select(D).where(D.tenant_id == ctx.tenant_id, type_ == resource_type, id_.in_(ids)))

    return fetch


def revinclude_reports_via_performer(param: str, resource_type: str, key):
    """_revinclude=DiagnosticReport:performer / :results-interpreter — reports with a
    row in the performer table pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_Pf.diagnostic_report_pk).where(
            _Pf.param == param, _Pf.reference_type == resource_type, _Pf.reference_id.in_(ids)
        )
        return await _fetch(session, select(D).where(D.tenant_id == ctx.tenant_id, D.id.in_(pks)))

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders DiagnosticReport rows."""
    from app.fhir.mappers.diagnostic_report import to_fhir_diagnostic_report
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "DiagnosticReport", lambda r: r.diagnostic_report_id, to_fhir_diagnostic_report, "diagnostic-reports"
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {"identifier": "`:identifier` — match the logical identifier of a target that has no resource here."}


@cache
def diagnostic_report_search() -> SearchRegistry:
    _register_kind()

    def token(name, description, expression, example):
        match, present, sort = _token_param(name)
        return SearchParam(name, "token", description, expression, match, present, _TOKEN, sort=sort, example=example)

    def column_ref(name, description, expression, prefix, targets, example, narrowed=None):
        match, present, chain, sort = _column_ref(prefix, targets, narrowed)
        modeled = [t for t in targets if t in _MODELED]
        return SearchParam(
            name, "reference", description, expression, match, present, _REFERENCE, targets=targets, chain=chain,
            chain_targets={t: _registry_of(t) for t in modeled}, sort=sort, example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    def reference(name, description, expression, example):
        # The R4 search-parameter name is also the `param` value in the reference table.
        targets = REFERENCE_TYPES[name]
        match, present, sort = _reference_param(name, targets)
        return SearchParam(
            name, "reference", description, expression, match, present, _REFERENCE, targets=targets, sort=sort,
            example=example, modifier_docs=_IDENTIFIER_DOC,
        )

    def performer(name, description, expression, example):
        match, present, chain, sort = _performer_param(name)
        modeled = [t for t in PERFORMER_TYPES if t in _MODELED]
        return SearchParam(
            name, "reference", description, expression, match, present, _REFERENCE, targets=PERFORMER_TYPES,
            chain=chain, chain_targets={t: _registry_of(t) for t in modeled}, sort=sort, example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    modeled_performers = [t for t in PERFORMER_TYPES if t in _MODELED]

    params = [
        SearchParam(
            "_id", "token", "Logical id of the resource (the public diagnostic report id)", "Resource.id",
            _id_match, lambda ctx: true(), frozenset({"not", "missing"}),
            sort=lambda: D.diagnostic_report_id, example="110001",
        ),
        SearchParam(
            "_lastUpdated", "date", "When the resource last changed (meta.lastUpdated)", "Resource.meta.lastUpdated",
            lambda v, m, ctx: date_match(last_updated(), v), lambda ctx: true(),
            sort=last_updated, example="ge2024-01-01",
        ),
        reference("based-on", "Reference to the service request", "DiagnosticReport.basedOn", "ServiceRequest/80001"),
        token(
            "category", "Which diagnostic discipline/department created the report", "DiagnosticReport.category",
            "http://terminology.hl7.org/CodeSystem/v2-0074|LAB",
        ),
        token("code", "The code for the report, as opposed to codes for the atomic results", "DiagnosticReport.code",
              "http://loinc.org|58410-2"),
        token("conclusion", "A coded conclusion (interpretation/impression) on the report", "DiagnosticReport.conclusionCode",
              "http://snomed.info/sct|419099009"),
        SearchParam(
            "date", "date", "The clinically relevant time of the report (a dateTime or a Period)",
            "DiagnosticReport.effective",
            _date_match, lambda ctx: or_(D.effective_date_start.is_not(None), D.effective_date_end.is_not(None)),
            sort=lambda: D.effective_date_start, example="ge2026-01-01",
        ),
        column_ref(
            "encounter", "The Encounter when the order was made", "DiagnosticReport.encounter", "encounter",
            ("Encounter",), "Encounter/20001",
        ),
        SearchParam(
            "identifier", "token", "An identifier for the report", "DiagnosticReport.identifier",
            _identifier_match, lambda ctx: _exists(_I), frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I), example="urn:reports|DR-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "issued", "date", "When the report was issued", "DiagnosticReport.issued",
            lambda v, m, ctx: date_match(D.issued, v), lambda ctx: D.issued.is_not(None),
            sort=lambda: D.issued, example="ge2026-01-01",
        ),
        reference("media", "A reference to the image source", "DiagnosticReport.media.link", "Media/1"),
        column_ref(
            "patient", "The subject of the report if a patient", "DiagnosticReport.subject.where(resolve() is Patient)",
            "subject", ("Patient",), "Patient/10001", narrowed="Patient",
        ),
        performer(
            "performer", "Who is responsible for the report", "DiagnosticReport.performer", "Practitioner/30001"
        ),
        reference("result", "Link to an atomic result (observation resource)", "DiagnosticReport.result", "Observation/160001"),
        performer(
            "results-interpreter", "Who was the source of the report's interpretation",
            "DiagnosticReport.resultsInterpreter", "Practitioner/30001",
        ),
        reference("specimen", "The specimen details", "DiagnosticReport.specimen", "Specimen/310001"),
        SearchParam(
            "status", "token",
            "registered | partial | preliminary | final | amended | corrected | appended | cancelled | "
            f"entered-in-error | unknown (system {_STATUS_SYSTEM})",
            "DiagnosticReport.status", _status_match, lambda ctx: D.status.is_not(None), frozenset({"not", "missing"}),
            sort=lambda: D.status, example="final",
        ),
        column_ref(
            "subject", "The subject of the report", "DiagnosticReport.subject", "subject", SUBJECT_TYPES,
            "Patient/10001",
        ),
    ]

    # One include per target type that is a resource here, so `_include=DiagnosticReport:performer`
    # brings in all of them and `DiagnosticReport:performer:Practitioner` just the Practitioners.
    performer_includes = tuple(
        IncludeTarget("DiagnosticReport", param, t, _include_performer(param, t))
        for param in ("performer", "results-interpreter")
        for t in modeled_performers
    )

    return SearchRegistry(
        resource_type="DiagnosticReport",
        params={p.name: p for p in params},
        # Σ elements in the R4 DiagnosticReport definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {"identifier", "status", "category", "code", "subject", "encounter", "effectiveDateTime",
             "effectivePeriod", "issued", "performer", "resultsInterpreter", "media", "conclusionCode"}
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "code"}),
        includes=(
            IncludeTarget("DiagnosticReport", "patient", "Patient", _include_column("subject", "Patient")),
            IncludeTarget("DiagnosticReport", "subject", "Patient", _include_column("subject", "Patient")),
            IncludeTarget("DiagnosticReport", "subject", "Location", _include_column("subject", "Location")),
            IncludeTarget("DiagnosticReport", "encounter", "Encounter", _include_column("encounter", "Encounter")),
            *performer_includes,
        ),
        # Procedure.reasonReference points here.
        revincludes=(*reason_procedure_revincludes("DiagnosticReport", lambda r: r.diagnostic_report_id),),
        default_sort=lambda: [D.diagnostic_report_id.desc()],
    )
