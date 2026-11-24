"""
FHIR R4 Specimen search parameters (https://www.hl7.org/fhir/R4/specimen.html#search) plus the
common `_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from specimen_search() below. Same
arrangement as app.repository.detected_issue.search (single references held as columns, one
shared token table, the repeating `parent` reference in one shared reference table), plus a
second identifier-shaped table for `container-id` and the `accession` identifier held as two
columns on the row.

Each parameter's SQL reads only the search index (SpecimenModel's columns and child tables, see
its docstring) — never `content`.
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
from app.repository._service_request_revinclude import (
    column_service_request_revincludes,
    performer_service_request_revincludes,
    specimen_service_request_revincludes,
)
from app.repository._diagnostic_report_revinclude import reference_report_revincludes
from app.repository._observation_revinclude import column_observation_revincludes
from app.models.specimen import (
    COLLECTOR_TYPES,
    REFERENCE_TYPES,
    SUBJECT_TYPES,
    SpecimenContainerIdentifier,
    SpecimenIdentifier,
    SpecimenModel,
    SpecimenReference,
    SpecimenStatus,
    SpecimenToken,
)

M = SpecimenModel
_I = SpecimenIdentifier
_Ci = SpecimenContainerIdentifier
_Tk = SpecimenToken
_R = SpecimenReference

# Specimen.status is a `code` from the R4 specimen-status system.
_STATUS_SYSTEM = "http://hl7.org/fhir/specimen-status"

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
    return exists(select(literal(1)).where(model.specimen_pk == M.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.specimen_pk == M.id, *conditions)
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
    return M.specimen_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the specimen-status system: `code` or `system|code`;
    another system or `|code` (no system) never matches; an unknown code matches nothing
    (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == SpecimenStatus(token.code)
    except ValueError:
        return false()


def _collected_match(value, modifier, ctx):
    # Specimen.collection.collected[x] is a dateTime or a Period: matched as the range it covers.
    return period_match(M.collected_start, M.collected_end, value)


def _accession_match(value, modifier, ctx):
    return token_match(M.accession_system, M.accession_value, value)


def _identifier_param(model, text_cols_doc=None):
    """(match, present, sort) for an Identifier search held in one identifier-shaped table
    (`identifier` and `container-id`)."""

    def match(value, modifier, ctx):
        if modifier == "text":
            return _exists(
                model,
                token_text_match(
                    (model.type_text_norm, model.type_display_norm), value
                ),
            )
        if modifier == "of-type":
            type_system, type_code, ident = parse_of_type(value)
            return _exists(
                model,
                model.type_system == type_system,
                model.type_code == type_code,
                model.value == ident,
            )
        return _exists(model, token_match(model.system, model.value, value))

    def present(ctx):
        return _exists(model)

    def sort():
        return _child_sort(model.value, model)

    return match, present, sort


def _token_param(param: str):
    """(match, present, sort) for one of the token parameters held in the
    shared token table, selected by its `param` value."""

    def match(value, modifier, ctx):
        return _exists(
            _Tk,
            _Tk.param == param,
            coded_token_match(
                _Tk.system,
                _Tk.code,
                value,
                modifier,
                (_Tk.text_norm, _Tk.display_norm),
            ),
        )

    def present(ctx):
        return _exists(_Tk, _Tk.param == param)

    def sort():
        return _child_sort(_Tk.code, _Tk, _Tk.param == param)

    return match, present, sort


# ── references held as columns: subject / patient / collector ────────────────


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    specimen row. `narrowed` restricts a multi-target element to one type (`patient` is
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


# ── parent: the shared reference table ───────────────────────────────────────


def _reference_param(param: str):
    """(match, present, chain, sort) for one of the reference parameters held
    in the shared reference table, selected by its `param` value."""
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
    """_include of a reference held as columns: the rows of `resource_type` these specimens
    point at."""

    async def fetch(session, ctx, specimens):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(r, id_)
            for r in specimens
            if getattr(r, type_) == resource_type and getattr(r, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_reference(param: str, resource_type: str):
    """_include of a reference-table parameter (`parent`): the rows of `resource_type`."""

    async def fetch(session, ctx, specimens):
        ids = select(_R.reference_id).where(
            _R.specimen_pk.in_({r.id for r in specimens}),
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


def revinclude_specimens_via_column(prefix: str, resource_type: str, key):
    """_revinclude=Specimen:subject / :patient / :collector — specimens whose column reference
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


def revinclude_specimens_via_reference(param: str, resource_type: str, key):
    """_revinclude=Specimen:parent — specimens with a row in the reference table pointing at one
    of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.specimen_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Specimen rows."""
    from app.fhir.mappers.specimen import to_fhir_specimen
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind("Specimen", lambda r: r.specimen_id, to_fhir_specimen, "specimens")
    )


# ── registry ─────────────────────────────────────────────────────────────────

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
def specimen_search() -> SearchRegistry:
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

    def identifier(name, description, expression, model, example):
        match, present, sort = _identifier_param(model)
        return SearchParam(
            name,
            "token",
            description,
            expression,
            match,
            present,
            _IDENTIFIER,
            sort=sort,
            example=example,
            modifier_docs=_TEXT_DOC,
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

    parent_match, parent_present, parent_chain, parent_sort = _reference_param("parent")
    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public specimen id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.specimen_id,
            example="310001",
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
            "accession",
            "token",
            "The accession number associated with the specimen",
            "Specimen.accessionIdentifier",
            _accession_match,
            lambda ctx: M.accession_value.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.accession_value,
            example="urn:accessions|ACC-1",
        ),
        token(
            "bodysite",
            "The code for the body site from where the specimen originated",
            "Specimen.collection.bodySite",
            "http://snomed.info/sct|368208006",
        ),
        SearchParam(
            "collected",
            "date",
            "The date the specimen was collected",
            "Specimen.collection.collected",
            _collected_match,
            lambda ctx: M.collected_start.is_not(None) | M.collected_end.is_not(None),
            sort=lambda: M.collected_start,
            example="ge2026-01-01",
        ),
        column_ref(
            "collector",
            "Who collected the specimen",
            "Specimen.collection.collector",
            "collector",
            COLLECTOR_TYPES,
            "Practitioner/30001",
        ),
        token(
            "container",
            "The kind of specimen container",
            "Specimen.container.type",
            "http://snomed.info/sct|434746001",
        ),
        identifier(
            "container-id",
            "The unique identifier associated with the specimen container",
            "Specimen.container.identifier",
            _Ci,
            "urn:containers|C-1",
        ),
        identifier(
            "identifier",
            "The unique identifier associated with the specimen",
            "Specimen.identifier",
            _I,
            "urn:specimens|SP-1",
        ),
        SearchParam(
            "parent",
            "reference",
            "The parent of the specimen",
            "Specimen.parent",
            parent_match,
            parent_present,
            _REFERENCE,
            targets=REFERENCE_TYPES["parent"],
            chain=parent_chain,
            chain_targets={"Specimen": _registry_of("Specimen")},
            sort=parent_sort,
            example="Specimen/310001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        column_ref(
            "patient",
            "The patient the specimen comes from",
            "Specimen.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        SearchParam(
            "status",
            "token",
            f"available | unavailable | unsatisfactory | entered-in-error (system {_STATUS_SYSTEM})",
            "Specimen.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="available",
        ),
        column_ref(
            "subject",
            "The subject of the specimen",
            "Specimen.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
        token(
            "type",
            "The specimen type",
            "Specimen.type",
            "http://terminology.hl7.org/CodeSystem/v2-0487|BLD",
        ),
    ]

    # One include per target type that is a resource here, so `_include=Specimen:subject`
    # brings in all of them and `Specimen:subject:Location` just the Locations.
    subject_includes = tuple(
        IncludeTarget("Specimen", "subject", t, _include_column("subject", t))
        for t in SUBJECT_TYPES
        if t in _MODELED
    )
    collector_includes = tuple(
        IncludeTarget("Specimen", "collector", t, _include_column("collector", t))
        for t in COLLECTOR_TYPES
        if t in _MODELED
    )

    return SearchRegistry(
        resource_type="Specimen",
        params={p.name: p for p in params},
        # Σ elements in the R4 Specimen definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "accessionIdentifier",
                "status",
                "type",
                "subject",
                "receivedTime",
                "collection",
                "condition",
            }
        ),
        # Specimen has no element with min cardinality 1.
        mandatory_elements=frozenset(),
        includes=(
            IncludeTarget(
                "Specimen", "patient", "Patient", _include_column("subject", "Patient")
            ),
            *subject_includes,
            *collector_includes,
            IncludeTarget(
                "Specimen",
                "parent",
                "Specimen",
                _include_reference("parent", "Specimen"),
            ),
        ),
        # Observation.specimen and DiagnosticReport.specimen point here, and a specimen derived
        # from another one points back at it (Specimen:parent).
        revincludes=(
            *specimen_service_request_revincludes(lambda s: s.specimen_id),
            *column_observation_revincludes(
                ("specimen",), "specimen", "Specimen", lambda r: r.specimen_id
            ),
            *reference_report_revincludes(
                "specimen", "Specimen", lambda r: r.specimen_id
            ),
            IncludeTarget(
                "Specimen",
                "parent",
                "Specimen",
                revinclude_specimens_via_reference(
                    "parent", "Specimen", lambda r: r.specimen_id
                ),
                reverse=True,
            ),
        ),
        default_sort=lambda: [M.specimen_id.desc()],
    )
