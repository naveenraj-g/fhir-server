"""
FHIR R4 Immunization search parameters
(https://www.hl7.org/fhir/R4/immunization.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
immunization_search() below. Same arrangement as
app.repository.diagnostic_report.search (references held as columns, shared
token table, child tables for the repeating references).

Each parameter's SQL reads only the search index (ImmunizationModel's columns
and child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.fhir.search import (
    IncludeTarget,
    MultiValueSort,
    SearchParam,
    SearchRegistry,
    normalize,
)
from app.fhir.search.sql import (
    coded_token_match,
    date_match,
    period_match,
    reference_match,
    string_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.repository._immunization_evaluation_revinclude import (
    column_evaluation_revincludes,
)
from app.repository._immunization_recommendation_revinclude import (
    support_recommendation_revincludes,
)
from app.repository._observation_revinclude import reference_observation_revincludes
from app.models.immunization import (
    PERFORMER_TYPES,
    REASON_TYPES,
    ImmunizationIdentifier,
    ImmunizationModel,
    ImmunizationPerformer,
    ImmunizationProtocol,
    ImmunizationReaction,
    ImmunizationReasonReference,
    ImmunizationStatus,
    ImmunizationToken,
)

M = ImmunizationModel
_I = ImmunizationIdentifier
_Tk = ImmunizationToken
_Pr = ImmunizationProtocol
_Rc = ImmunizationReaction
_Pf = ImmunizationPerformer
_Rr = ImmunizationReasonReference
# Immunization.status is a `code` from the event-status code system.
_STATUS_SYSTEM = "http://hl7.org/fhir/event-status"

# Reference targets that are searchable resources on this server: the model to
# join for chaining / `_include`, and its registry.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = {
    "Observation": (
        "app.models.observation",
        "ObservationModel",
        "observation_id",
        "app.repository.observation.search",
        "observation_search",
    ),
    "Patient": (
        "app.models.patient",
        "PatientModel",
        "patient_id",
        "app.repository.patient.search",
        "patient_search",
    ),
    "Practitioner": (
        "app.models.practitioner",
        "PractitionerModel",
        "practitioner_id",
        "app.repository.practitioner.search",
        "practitioner_search",
    ),
    "PractitionerRole": (
        "app.models.practitioner_role",
        "PractitionerRoleModel",
        "practitioner_role_id",
        "app.repository.practitioner_role.search",
        "practitioner_role_search",
    ),
    "Organization": (
        "app.models.organization",
        "OrganizationModel",
        "organization_id",
        "app.repository.organization.search",
        "organization_search",
    ),
    "Location": (
        "app.models.location",
        "LocationModel",
        "location_id",
        "app.repository.location.search",
        "location_search",
    ),
    "Condition": (
        "app.models.condition",
        "ConditionModel",
        "condition_id",
        "app.repository.condition.search",
        "condition_search",
    ),
    "DiagnosticReport": (
        "app.models.diagnostic_report",
        "DiagnosticReportModel",
        "diagnostic_report_id",
        "app.repository.diagnostic_report.search",
        "diagnostic_report_search",
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
    return exists(select(literal(1)).where(model.immunization_pk == M.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.immunization_pk == M.id, *conditions)
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
    return M.immunization_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the event-status system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an unknown
    code matches nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == ImmunizationStatus(token.code)
    except ValueError:
        return false()


def _date_match(value, modifier, ctx):
    # Immunization.occurrence[x] as a dateTime: matched as the range it covers.
    return period_match(M.occurrence_date_start, M.occurrence_date_end, value)


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


# ── references held as columns: patient / location / manufacturer ────────────


def _column_ref(prefix: str, targets: tuple[str, ...]):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*`
    columns on the immunization row."""
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
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return or_(ref.is_not(None), ident_value.is_not(None))

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# ── references held in child tables: performer / reason-reference / reaction ──


def _child_ref(model, targets: tuple[str, ...], prefix: str = "reference"):
    """(match, present, chain, sort) for a Reference held in one child table
    (one row per Reference), columns `{prefix}_reference/_type/_id/_identifier_*`."""
    ref, type_, id_ = (
        getattr(model, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(model, f"{prefix}_identifier_system"),
        getattr(model, f"{prefix}_identifier_value"),
    )

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return _exists(
                model, token_condition(ident_system, ident_value, parse_token(value))
            )
        return _exists(
            model, reference_match(type_, id_, ref, value, modifier, ctx, targets, str)
        )

    def present(ctx):
        return _exists(model, or_(ref.is_not(None), ident_value.is_not(None)))

    def chain(target, inner, ctx):
        return _exists(model, type_ == target, id_.in_(_referenced(target, inner, ctx)))

    def sort():
        return _child_sort(id_, model)

    return match, present, chain, sort


# ── string: series / lot-number ──────────────────────────────────────────────


def _series_match(value, modifier, ctx):
    return _exists(_Pr, string_match(_Pr.series, _Pr.series_norm, value, modifier))


def _lot_match(value, modifier, ctx):
    return string_match(M.lot_number, M.lot_number_norm, value, modifier)


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
    """_include of a reference held as columns (`patient`, `location`,
    `manufacturer`): the rows of `resource_type` these immunizations point at."""

    async def fetch(session, ctx, immunizations):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(r, id_)
            for r in immunizations
            if getattr(r, type_) == resource_type and getattr(r, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_child(model, resource_type: str):
    """_include of a reference held in a child table (`performer`, `reason-reference`)."""

    async def fetch(session, ctx, immunizations):
        ids = select(model.reference_id).where(
            model.immunization_pk.in_({r.id for r in immunizations}),
            model.reference_type == resource_type,
            model.reference_id.is_not(None),
        )
        return await _load(
            session,
            ctx,
            resource_type,
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


def _include_reaction(resource_type: str):
    """_include=Immunization:reaction — the Observations the reactions point at."""

    async def fetch(session, ctx, immunizations):
        ids = select(_Rc.detail_id).where(
            _Rc.immunization_pk.in_({r.id for r in immunizations}),
            _Rc.detail_type == resource_type,
            _Rc.detail_id.is_not(None),
        )
        return await _load(
            session,
            ctx,
            resource_type,
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


def revinclude_immunizations_via_reaction(key):
    """_revinclude=Immunization:reaction — immunizations with a reaction whose detail is
    one of these Observations."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_Rc.immunization_pk).where(
            _Rc.detail_type == "Observation", _Rc.detail_id.in_(ids)
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def revinclude_immunizations_via_column(prefix: str, resource_type: str, key):
    """_revinclude=Immunization:patient / :location / :manufacturer — immunizations
    whose column reference points at one of these rows (matched on the public id
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


def revinclude_immunizations_via_child(model, resource_type: str, key):
    """_revinclude=Immunization:performer / :reason-reference — immunizations with a
    row in the child table pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(model.immunization_pk).where(
            model.reference_type == resource_type, model.reference_id.in_(ids)
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Immunization rows."""
    from app.fhir.mappers.immunization import to_fhir_immunization
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "Immunization",
            lambda r: r.immunization_id,
            to_fhir_immunization,
            "immunizations",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def immunization_search() -> SearchRegistry:
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

    def column_ref(name, description, expression, prefix, targets, example):
        match, present, chain, sort = _column_ref(prefix, targets)
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

    def child_ref(
        name, description, expression, model, targets, example, prefix="reference"
    ):
        match, present, chain, sort = _child_ref(model, targets, prefix)
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
            "Logical id of the resource (the public immunization id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.immunization_id,
            example="330001",
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
            "Vaccination (non)-Administration Date",
            "Immunization.occurrence",
            _date_match,
            lambda ctx: M.occurrence_date_start.is_not(None),
            sort=lambda: M.occurrence_date_start,
            example="ge2026-01-01",
        ),
        SearchParam(
            "identifier",
            "token",
            "Business identifier",
            "Immunization.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:immunizations|IM-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        column_ref(
            "location",
            "The service delivery location or facility in which the vaccine was / was to be administered",
            "Immunization.location",
            "location",
            ("Location",),
            "Location/230001",
        ),
        SearchParam(
            "lot-number",
            "string",
            "Vaccine Lot Number",
            "Immunization.lotNumber",
            _lot_match,
            lambda ctx: M.lot_number.is_not(None),
            frozenset({"exact", "contains", "missing"}),
            sort=lambda: M.lot_number_norm,
            example="AAJN11K",
        ),
        column_ref(
            "manufacturer",
            "Vaccine Manufacturer",
            "Immunization.manufacturer",
            "manufacturer",
            ("Organization",),
            "Organization/190001",
        ),
        column_ref(
            "patient",
            "The patient for the vaccination record",
            "Immunization.patient",
            "patient",
            ("Patient",),
            "Patient/10001",
        ),
        child_ref(
            "performer",
            "The practitioner or organization who played a role in the vaccination",
            "Immunization.performer.actor",
            _Pf,
            PERFORMER_TYPES,
            "Practitioner/30001",
        ),
        child_ref(
            "reaction",
            "Additional information on reaction",
            "Immunization.reaction.detail",
            _Rc,
            ("Observation",),
            "Observation/160001",
            prefix="detail",
        ),
        SearchParam(
            "reaction-date",
            "date",
            "When reaction started",
            "Immunization.reaction.date",
            lambda v, m, ctx: _exists(
                _Rc, period_match(_Rc.date_start, _Rc.date_end, v)
            ),
            lambda ctx: _exists(_Rc, _Rc.date_start.is_not(None)),
            sort=lambda: _child_sort(_Rc.date_start, _Rc),
            example="ge2026-01-01",
        ),
        token(
            "reason-code",
            "Reason why the vaccine was administered",
            "Immunization.reasonCode",
            "http://snomed.info/sct|429060002",
        ),
        child_ref(
            "reason-reference",
            "Why immunization occurred",
            "Immunization.reasonReference",
            _Rr,
            REASON_TYPES,
            "Condition/120001",
        ),
        SearchParam(
            "series",
            "string",
            "The series being followed by the provider",
            "Immunization.protocolApplied.series",
            _series_match,
            lambda ctx: _exists(_Pr),
            frozenset({"exact", "contains", "missing"}),
            sort=lambda: _child_sort(_Pr.series_norm, _Pr),
            example="2-dose",
        ),
        SearchParam(
            "status",
            "token",
            f"completed | entered-in-error | not-done (system {_STATUS_SYSTEM})",
            "Immunization.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="completed",
        ),
        token(
            "status-reason",
            "Reason why the vaccine was not administered",
            "Immunization.statusReason",
            "http://terminology.hl7.org/CodeSystem/v3-ActReason|PATOBJ",
        ),
        token(
            "target-disease",
            "The target disease the dose is being administered against",
            "Immunization.protocolApplied.targetDisease",
            "http://snomed.info/sct|40468003",
        ),
        token(
            "vaccine-code",
            "Vaccine Product Administered",
            "Immunization.vaccineCode",
            "http://hl7.org/fhir/sid/cvx|140",
        ),
    ]

    # One include per target type that is a resource here, so `_include=Immunization:performer`
    # brings in all of them and `Immunization:performer:Practitioner` just the Practitioners.
    performer_includes = tuple(
        IncludeTarget("Immunization", "performer", t, _include_child(_Pf, t))
        for t in PERFORMER_TYPES
        if t in _MODELED
    )
    reason_includes = tuple(
        IncludeTarget("Immunization", "reason-reference", t, _include_child(_Rr, t))
        for t in REASON_TYPES
        if t in _MODELED
    )

    return SearchRegistry(
        resource_type="Immunization",
        params={p.name: p for p in params},
        # Σ elements in the R4 Immunization definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "status",
                "vaccineCode",
                "patient",
                "occurrenceDateTime",
                "occurrenceString",
                "primarySource",
                "performer",
                "note",
                "isSubpotent",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset(
            {
                "status",
                "vaccineCode",
                "patient",
                "occurrenceDateTime",
                "occurrenceString",
            }
        ),
        includes=(
            IncludeTarget(
                "Immunization",
                "patient",
                "Patient",
                _include_column("patient", "Patient"),
            ),
            IncludeTarget(
                "Immunization",
                "location",
                "Location",
                _include_column("location", "Location"),
            ),
            IncludeTarget(
                "Immunization",
                "manufacturer",
                "Organization",
                _include_column("manufacturer", "Organization"),
            ),
            *performer_includes,
            *reason_includes,
            IncludeTarget(
                "Immunization",
                "reaction",
                "Observation",
                _include_reaction("Observation"),
            ),
        ),
        revincludes=(
            *support_recommendation_revincludes(
                "Immunization", lambda r: r.immunization_id
            ),
            *reference_observation_revincludes(
                "part-of", "Immunization", lambda r: r.immunization_id
            ),
            *column_evaluation_revincludes(
                "immunization-event",
                "immunization_event",
                "Immunization",
                lambda r: r.immunization_id,
            ),
        ),
        default_sort=lambda: [M.immunization_id.desc()],
    )
