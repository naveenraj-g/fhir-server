"""
FHIR R4 MedicationStatement search parameters
(https://www.hl7.org/fhir/R4/medicationstatement.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`, `_include` /
`_revinclude`, and the OpenAPI docs all come from medication_statement_search() below. Same
arrangement as app.repository.medication_request.search (references held as columns, one shared
token table) with a shared reference table for the repeating `part-of`.

Each parameter's SQL reads only the search index (MedicationStatementModel's columns and child
tables, see its docstring) - never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.repository._search_targets import MODELED
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
from app.models.medication_statement import (
    CONTEXT_TYPES,
    MEDICATION_TYPES,
    REFERENCE_TYPES,
    SOURCE_TYPES,
    SUBJECT_TYPES,
    MedicationStatementIdentifier,
    MedicationStatementModel,
    MedicationStatementReference,
    MedicationStatementStatus,
    MedicationStatementToken,
)

M = MedicationStatementModel
_I = MedicationStatementIdentifier
_Tk = MedicationStatementToken
_R = MedicationStatementReference

# MedicationStatement.status is a `code` from the R4 medication-statement-status system.
_STATUS_SYSTEM = "http://hl7.org/fhir/CodeSystem/medication-statement-status"


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
        select(literal(1)).where(model.medication_statement_pk == M.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.medication_statement_pk == M.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(M.updated_at, M.created_at)


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition. Does not correlate to the
    outer row - it ranges over the referenced resource."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return M.medication_statement_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the medication-statement-status system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an unknown code matches
    nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == MedicationStatementStatus(token.code)
    except ValueError:
        return false()


def _effective_match(value, modifier, ctx):
    # MedicationStatement.effective[x] is a dateTime or a Period: matched as the range it covers.
    return period_match(M.effective_start, M.effective_end, value)


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


# -- references held as columns: subject / patient / context / source / medication ------------


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    medication_statement row. `narrowed` restricts a multi-target element to one type
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


# -- part-of: one row per Reference in the shared reference table -----------------------------


def _reference_param(param: str):
    """(match, present, chain, sort) for one of the reference parameters held in the shared
    reference table, selected by its `param` value."""
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
    """_include of a reference held as columns: the rows of `resource_type` these medication
    statements point at."""

    async def fetch(session, ctx, statements):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(s, id_)
            for s in statements
            if getattr(s, type_) == resource_type and getattr(s, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_reference(param: str, resource_type: str):
    """_include of a reference held in the shared reference table: the rows of `resource_type`
    these statements' `param` references point at."""

    async def fetch(session, ctx, statements):
        ids = select(_R.reference_id).where(
            _R.medication_statement_pk.in_({s.id for s in statements}),
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


def revinclude_statements_via_column(prefix: str, resource_type: str, key):
    """_revinclude=MedicationStatement:subject / :patient / :context / :source / :medication -
    medication statements whose column reference points at one of these rows (matched on the
    public id `key(row)`). Declared on the registry of each target type."""

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


def revinclude_statements_via_reference(param: str, resource_type: str, key):
    """_revinclude=MedicationStatement:part-of - medication statements with a reference row of
    `param` pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.medication_statement_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders MedicationStatement rows."""
    from app.fhir.mappers.medication_statement import to_fhir_medication_statement
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "MedicationStatement",
            lambda r: r.medication_statement_id,
            to_fhir_medication_statement,
            "medication-statements",
        )
    )


# -- registry ------------------------------------------------------------------------------

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER = frozenset({"text", "not", "of-type", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}
_TEXT_DOC = {
    "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
}


@cache
def medication_statement_search() -> SearchRegistry:
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

    def table_ref(name, description, expression, example):
        match, present, chain, sort = _reference_param(name)
        targets = REFERENCE_TYPES[name]
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
            "Logical id of the resource (the public medication statement id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.medication_statement_id,
            example="500001",
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
            "category",
            "Returns statements of this category of medicationstatement",
            "MedicationStatement.category",
            "http://terminology.hl7.org/CodeSystem/medication-statement-category|inpatient",
        ),
        token(
            "code",
            "Return statements of this medication code",
            "(MedicationStatement.medication as CodeableConcept)",
            "http://snomed.info/sct|387458008",
        ),
        column_ref(
            "context",
            "Returns statements for a specific context (episode or episode of Care).",
            "MedicationStatement.context",
            "context",
            CONTEXT_TYPES,
            "Encounter/20001",
        ),
        SearchParam(
            "effective",
            "date",
            "Date when patient was taking (or not taking) the medication",
            "MedicationStatement.effective",
            _effective_match,
            lambda ctx: or_(
                M.effective_start.is_not(None), M.effective_end.is_not(None)
            ),
            sort=lambda: M.effective_start,
            example="ge2026-01-01",
        ),
        SearchParam(
            "identifier",
            "token",
            "Return statements with this external identifier",
            "MedicationStatement.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            _IDENTIFIER,
            sort=lambda: _child_sort(_I.value, _I),
            example="https://fhir-server.dev/fhir/identifier-system/medication-statement-id|MS-1",
            modifier_docs=_TEXT_DOC,
        ),
        column_ref(
            "medication",
            "Return statements of this medication reference",
            "(MedicationStatement.medication as Reference)",
            "medication",
            MEDICATION_TYPES,
            "Medication/250001",
        ),
        table_ref(
            "part-of",
            "Returns statements that are part of another event.",
            "MedicationStatement.partOf",
            "Observation/160001",
        ),
        column_ref(
            "patient",
            "Returns statements for a specific patient.",
            "MedicationStatement.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        column_ref(
            "source",
            "Who or where the information in the statement came from",
            "MedicationStatement.informationSource",
            "source",
            SOURCE_TYPES,
            "Practitioner/30001",
        ),
        SearchParam(
            "status",
            "token",
            "Return statements that match the given status",
            "MedicationStatement.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="active",
        ),
        column_ref(
            "subject",
            "The identity of a patient, animal or group to list statements for",
            "MedicationStatement.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
    ]

    def column_includes(name, prefix, targets):
        return tuple(
            IncludeTarget("MedicationStatement", name, t, _include_column(prefix, t))
            for t in targets
            if t in _MODELED
        )

    def table_includes(param):
        return tuple(
            IncludeTarget("MedicationStatement", param, t, _include_reference(param, t))
            for t in REFERENCE_TYPES[param]
            if t in _MODELED
        )

    return SearchRegistry(
        resource_type="MedicationStatement",
        params={p.name: p for p in params},
        # Σ elements in the R4 MedicationStatement definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "basedOn",
                "partOf",
                "status",
                "category",
                "medicationCodeableConcept",
                "medicationReference",
                "subject",
                "context",
                "effectiveDateTime",
                "effectivePeriod",
                "dateAsserted",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset(
            {"status", "medicationCodeableConcept", "medicationReference", "subject"}
        ),
        includes=(
            IncludeTarget(
                "MedicationStatement",
                "patient",
                "Patient",
                _include_column("subject", "Patient"),
            ),
            *column_includes("subject", "subject", SUBJECT_TYPES),
            *column_includes("context", "context", CONTEXT_TYPES),
            *column_includes("source", "source", SOURCE_TYPES),
            *column_includes("medication", "medication", MEDICATION_TYPES),
            *table_includes("part-of"),
        ),
        # Filled in by the registries of the resources a statement points at
        # (see app.repository._medication_statement_revinclude), and by MedicationStatement
        # itself for `part-of`.
        revincludes=(*table_revincludes_self(),),
        default_sort=lambda: [M.medication_statement_id.desc()],
    )


def table_revincludes_self() -> tuple[IncludeTarget, ...]:
    """MedicationStatement:part-of on MedicationStatement itself: the statements that are part of
    the matched statements."""
    return (
        IncludeTarget(
            "MedicationStatement",
            "part-of",
            "MedicationStatement",
            revinclude_statements_via_reference(
                "part-of", "MedicationStatement", lambda x: x.medication_statement_id
            ),
            reverse=True,
        ),
    )
