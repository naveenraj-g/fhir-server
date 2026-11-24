"""
FHIR R4 Procedure search parameters
(https://www.hl7.org/fhir/R4/procedure.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
procedure_search() below. Same arrangement as app.repository.condition.search
and app.repository.encounter.search (references held as columns, shared token and
reference tables); `instantiates-uri` is the engine's first `uri` search
(app.fhir.search.sql.uri_match) and `instantiates-canonical` its first search over
canonical URLs.

Each parameter's SQL reads only the search index (ProcedureModel's columns and
child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

import importlib
import re
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.repository._flag_revinclude import column_flag_revincludes
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
    uri_match,
)
from app.fhir.search.values import like_escape, parse_of_type, parse_token
from app.repository._medication_statement_revinclude import (
    reference_medication_statement_revincludes,
)
from app.repository._questionnaire_response_revinclude import (
    reference_questionnaire_response_revincludes,
)
from app.repository._appointment_revinclude import reason_appointment_revincludes
from app.repository._encounter_revinclude import reference_encounter_revincludes
from app.repository._observation_revinclude import reference_observation_revincludes
from app.models.procedure import (
    PERFORMER_TYPES,
    REFERENCE_TYPES,
    SUBJECT_TYPES,
    ProcedureIdentifier,
    ProcedureInstantiatesUri,
    ProcedureModel,
    ProcedurePerformer,
    ProcedureReference,
    ProcedureStatus,
    ProcedureToken,
)

P = ProcedureModel
_I = ProcedureIdentifier
_Tk = ProcedureToken
_R = ProcedureReference
_Pf = ProcedurePerformer
_U = ProcedureInstantiatesUri
_STATUS_SYSTEM = "http://hl7.org/fhir/event-status"
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
    return exists(select(literal(1)).where(model.procedure_pk == P.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.procedure_pk == P.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(P.updated_at, P.created_at)


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
    return P.procedure_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the event-status system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an unknown
    code matches nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return P.status.is_not(None)
    try:
        return P.status == ProcedureStatus(token.code)
    except ValueError:
        return false()


def _date_match(value, modifier, ctx):
    # Procedure.performed[x] as a dateTime or a Period: matched as a range.
    return period_match(P.performed_date_start, P.performed_date_end, value)


# ── identifier / the three token parameters ──────────────────────────────────


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


# ── references held as columns: subject / patient / encounter / location ─────


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*`
    columns on the procedure row. `narrowed` restricts a multi-target element to
    one type (`patient` is `subject` resolved to a Patient)."""
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
        # `modifier` is a target type (subject:Patient=10001) or None; a bare id
        # with several targets is ambiguous and is rejected by reference_target().
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return and_(or_(ref.is_not(None), ident_value.is_not(None)), *type_filter)

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# ── references held in the reference table: based-on / part-of / reason-reference ──


def _reference_param(param: str, targets: tuple[str, ...]):
    """(match, present, chain, sort) for one of the reference parameters held
    in the shared reference table, selected by its `param` value."""

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


def _canonical_param():
    """`instantiates-canonical`: the values are canonical URLs, optionally
    versioned (`url|1.0`). A search value matches a stored canonical equal to it;
    an unversioned absolute URL also matches the stored versions of that URL; a
    relative `Type/<id>` matches by its resolved type and id."""
    param = "instantiates-canonical"
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

    return (
        match,
        present,
        lambda: _child_sort(_R.reference_reference, _R, _R.param == param),
    )


# ── performer ────────────────────────────────────────────────────────────────


def _performer_match(value, modifier, ctx):
    if modifier == "identifier":
        return _exists(
            _Pf,
            token_condition(
                _Pf.reference_identifier_system,
                _Pf.reference_identifier_value,
                parse_token(value),
            ),
        )
    return _exists(
        _Pf,
        reference_match(
            _Pf.reference_type,
            _Pf.reference_id,
            _Pf.reference_reference,
            value,
            modifier,
            ctx,
            PERFORMER_TYPES,
            str,
        ),
    )


def _performer_present(ctx):
    return _exists(
        _Pf,
        or_(
            _Pf.reference_reference.is_not(None),
            _Pf.reference_identifier_value.is_not(None),
        ),
    )


def _performer_chain(target, inner, ctx):
    return _exists(
        _Pf,
        _Pf.reference_type == target,
        _Pf.reference_id.in_(_referenced(target, inner, ctx)),
    )


# ── instantiates-uri ─────────────────────────────────────────────────────────


def _uri_match(value, modifier, ctx):
    return _exists(_U, uri_match(_U.uri, value, modifier))


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
    """_include of a reference held as columns (`subject`, `patient`, `encounter`,
    `location`): the rows of `resource_type` these procedures point at."""

    async def fetch(session, ctx, procedures):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(p, id_)
            for p in procedures
            if getattr(p, type_) == resource_type and getattr(p, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_child(model, resource_type: str, *conditions):
    """_include of a reference held in a child table (performer, part-of,
    reason-reference)."""

    async def fetch(session, ctx, procedures):
        ids = select(model.reference_id).where(
            model.procedure_pk.in_({p.id for p in procedures}),
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


def revinclude_procedures_via_column(prefix: str, resource_type: str, key):
    """_revinclude=Procedure:subject / :patient / :encounter / :location —
    procedures whose column reference points at one of these rows (matched on the
    public id `key(row)`). Declared on the registry of each target type."""

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


def revinclude_procedures_via_child(model, resource_type: str, key, *conditions):
    """_revinclude=Procedure:performer / :part-of / :reason-reference —
    procedures with a row in `model` pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(model.procedure_pk).where(
            model.reference_type == resource_type,
            model.reference_id.in_(ids),
            *conditions,
        )
        return await _fetch(
            session, select(P).where(P.tenant_id == ctx.tenant_id, P.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Procedure rows."""
    from app.fhir.mappers.procedure import to_fhir_procedure
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "Procedure", lambda p: p.procedure_id, to_fhir_procedure, "procedures"
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def procedure_search() -> SearchRegistry:
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

    def reference(name, description, expression, example):
        # The R4 search-parameter name is also the `param` value in the reference table.
        targets = REFERENCE_TYPES[name]
        match, present, chain, sort = _reference_param(name, targets)
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

    canonical_match, canonical_present, canonical_sort = _canonical_param()
    modeled_performers = [t for t in PERFORMER_TYPES if t in _MODELED]

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public procedure id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.procedure_id,
            example="100001",
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
        reference(
            "based-on",
            "A request for this procedure",
            "Procedure.basedOn",
            "ServiceRequest/80001",
        ),
        token(
            "category",
            "Classification of the procedure",
            "Procedure.category",
            "http://snomed.info/sct|387713003",
        ),
        token(
            "code",
            "A code to identify a procedure",
            "Procedure.code",
            "http://snomed.info/sct|80146002",
        ),
        SearchParam(
            "date",
            "date",
            "When the procedure was performed (a dateTime or a Period)",
            "Procedure.performed",
            _date_match,
            lambda ctx: or_(
                P.performed_date_start.is_not(None), P.performed_date_end.is_not(None)
            ),
            sort=lambda: P.performed_date_start,
            example="ge2026-01-01",
        ),
        column_ref(
            "encounter",
            "Encounter created as part of",
            "Procedure.encounter",
            "encounter",
            ("Encounter",),
            "Encounter/20001",
        ),
        SearchParam(
            "identifier",
            "token",
            "A unique identifier for a procedure",
            "Procedure.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:procedures|PR-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "instantiates-canonical",
            "reference",
            "Instantiates FHIR protocol or definition (a canonical URL)",
            "Procedure.instantiatesCanonical",
            canonical_match,
            canonical_present,
            frozenset({"missing"}),
            targets=REFERENCE_TYPES["instantiates-canonical"],
            sort=canonical_sort,
            example="http://example.org/fhir/PlanDefinition/knee-replacement",
            modifier_docs={
                "missing": "`:missing=true` — resources with no canonical for this parameter; `:missing=false` — resources that have one."
            },
        ),
        SearchParam(
            "instantiates-uri",
            "uri",
            "Instantiates external protocol or definition",
            "Procedure.instantiatesUri",
            _uri_match,
            lambda ctx: _exists(_U),
            frozenset({"above", "below", "missing"}),
            sort=lambda: _child_sort(_U.uri, _U),
            example="http://example.org/protocols/knee",
            modifier_docs={
                "below": "`:below` — stored URIs that start with the value (`http://acme.org/p` finds `http://acme.org/p/1`).",
                "above": "`:above` — stored URIs that are a prefix of the value.",
            },
        ),
        column_ref(
            "location",
            "Where the procedure happened",
            "Procedure.location",
            "location",
            ("Location",),
            "Location/230001",
        ),
        reference(
            "part-of",
            "A larger event of which this particular procedure is a component",
            "Procedure.partOf",
            "Procedure/100001",
        ),
        column_ref(
            "patient",
            "Search by subject - a patient",
            "Procedure.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        SearchParam(
            "performer",
            "reference",
            "Who performed the procedure (the performer's actor)",
            "Procedure.performer.actor",
            _performer_match,
            _performer_present,
            _REFERENCE,
            targets=PERFORMER_TYPES,
            chain=_performer_chain,
            chain_targets={t: _registry_of(t) for t in modeled_performers},
            sort=lambda: _child_sort(_Pf.reference_id, _Pf),
            example="Practitioner/30001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        token(
            "reason-code",
            "Reason the procedure was performed (coded)",
            "Procedure.reasonCode",
            "http://snomed.info/sct|396275006",
        ),
        reference(
            "reason-reference",
            "The justification that the procedure was performed",
            "Procedure.reasonReference",
            "Condition/120001",
        ),
        SearchParam(
            "status",
            "token",
            "preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown "
            f"(system {_STATUS_SYSTEM})",
            "Procedure.status",
            _status_match,
            lambda ctx: P.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.status,
            example="completed",
        ),
        column_ref(
            "subject",
            "Search by subject",
            "Procedure.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
    ]

    performer_includes = tuple(
        IncludeTarget("Procedure", "performer", t, _include_child(_Pf, t))
        for t in modeled_performers
    )
    reason_includes = tuple(
        IncludeTarget(
            "Procedure",
            "reason-reference",
            t,
            _include_child(_R, t, _R.param == "reason-reference"),
        )
        for t in ("Condition", "Procedure", "DiagnosticReport", "Observation")
    )

    return SearchRegistry(
        resource_type="Procedure",
        params={p.name: p for p in params},
        # Σ elements in the R4 Procedure definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "instantiatesCanonical",
                "instantiatesUri",
                "basedOn",
                "partOf",
                "status",
                "statusReason",
                "category",
                "code",
                "subject",
                "encounter",
                "performedDateTime",
                "performedPeriod",
                "performedString",
                "performedAge",
                "performedRange",
                "recorder",
                "asserter",
                "performer",
                "location",
                "reasonCode",
                "reasonReference",
                "bodySite",
                "outcome",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "subject"}),
        includes=(
            IncludeTarget(
                "Procedure", "patient", "Patient", _include_column("subject", "Patient")
            ),
            IncludeTarget(
                "Procedure", "subject", "Patient", _include_column("subject", "Patient")
            ),
            IncludeTarget(
                "Procedure",
                "encounter",
                "Encounter",
                _include_column("encounter", "Encounter"),
            ),
            IncludeTarget(
                "Procedure",
                "location",
                "Location",
                _include_column("location", "Location"),
            ),
            *performer_includes,
            IncludeTarget(
                "Procedure",
                "based-on",
                "ServiceRequest",
                _include_child(_R, "ServiceRequest", _R.param == "based-on"),
            ),
            IncludeTarget(
                "Procedure",
                "based-on",
                "CarePlan",
                _include_child(_R, "CarePlan", _R.param == "based-on"),
            ),
            IncludeTarget(
                "Procedure",
                "part-of",
                "Procedure",
                _include_child(_R, "Procedure", _R.param == "part-of"),
            ),
            *reason_includes,
        ),
        # Encounter.diagnosis / .reasonReference and Appointment.reasonReference point here,
        # and a Procedure that is part of, or justified by, another one points back at it.
        revincludes=(
            *column_flag_revincludes(
                ("subject",), "subject", "Procedure", lambda x: x.procedure_id
            ),
            *reference_medication_statement_revincludes(
                "part-of", "Procedure", lambda x: x.procedure_id
            ),
            *reference_questionnaire_response_revincludes(
                "part-of", "Procedure", lambda x: x.procedure_id
            ),
            *reference_encounter_revincludes("Procedure", lambda p: p.procedure_id),
            *reference_observation_revincludes(
                "part-of", "Procedure", lambda p: p.procedure_id
            ),
            *reason_appointment_revincludes("Procedure", lambda p: p.procedure_id),
            IncludeTarget(
                "Procedure",
                "part-of",
                "Procedure",
                revinclude_procedures_via_child(
                    _R, "Procedure", lambda p: p.procedure_id, _R.param == "part-of"
                ),
                reverse=True,
            ),
            IncludeTarget(
                "Procedure",
                "reason-reference",
                "Procedure",
                revinclude_procedures_via_child(
                    _R,
                    "Procedure",
                    lambda p: p.procedure_id,
                    _R.param == "reason-reference",
                ),
                reverse=True,
            ),
        ),
        default_sort=lambda: [P.procedure_id.desc()],
    )
