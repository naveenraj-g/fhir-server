"""
FHIR R4 ServiceRequest search parameters
(https://www.hl7.org/fhir/R4/servicerequest.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
service_request_search() below. Same arrangement as app.repository.procedure.search
and app.repository.observation.search (references held as columns, shared token and
reference tables); `instantiates-uri` and `instantiates-canonical` work as on Procedure.

Each parameter's SQL reads only the search index (ServiceRequestModel's columns and
child tables, see its docstring) - never `content`.
"""

from __future__ import annotations

import importlib
import re
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
    uri_match,
)
from app.fhir.search.values import like_escape, parse_of_type, parse_token
from app.repository._diagnostic_report_revinclude import (
    reference_report_revincludes,
)
from app.repository._encounter_revinclude import reference_encounter_revincludes
from app.repository._observation_revinclude import reference_observation_revincludes
from app.repository._procedure_revinclude import based_on_procedure_revincludes
from app.models.service_request import (
    PERFORMER_TYPES,
    REFERENCE_TYPES,
    REQUESTER_TYPES,
    SUBJECT_TYPES,
    ServiceRequestIdentifier,
    ServiceRequestInstantiatesUri,
    ServiceRequestIntent,
    ServiceRequestModel,
    ServiceRequestPerformer,
    ServiceRequestPriority,
    ServiceRequestReference,
    ServiceRequestStatus,
    ServiceRequestToken,
)

P = ServiceRequestModel
_I = ServiceRequestIdentifier
_Tk = ServiceRequestToken
_R = ServiceRequestReference
_Pf = ServiceRequestPerformer
_U = ServiceRequestInstantiatesUri
_STATUS_SYSTEM = "http://hl7.org/fhir/request-status"
_INTENT_SYSTEM = "http://hl7.org/fhir/request-intent"
_PRIORITY_SYSTEM = "http://hl7.org/fhir/request-priority"
_ABSOLUTE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _modeled(module: str, cls: str, id_col: str, search_module: str, factory: str):
    return (module, cls, id_col, search_module, factory)


# Reference targets that are searchable resources on this server: the model to
# join for chaining / `_include`, and its registry.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = {
    "ServiceRequest": _modeled(
        "app.models.service_request",
        "ServiceRequestModel",
        "service_request_id",
        "app.repository.service_request.search",
        "service_request_search",
    ),
    "Specimen": _modeled(
        "app.models.specimen",
        "SpecimenModel",
        "specimen_id",
        "app.repository.specimen.search",
        "specimen_search",
    ),
    "Patient": _modeled(
        "app.models.patient",
        "PatientModel",
        "patient_id",
        "app.repository.patient.search",
        "patient_search",
    ),
    "Practitioner": _modeled(
        "app.models.practitioner",
        "PractitionerModel",
        "practitioner_id",
        "app.repository.practitioner.search",
        "practitioner_search",
    ),
    "PractitionerRole": _modeled(
        "app.models.practitioner_role",
        "PractitionerRoleModel",
        "practitioner_role_id",
        "app.repository.practitioner_role.search",
        "practitioner_role_search",
    ),
    "RelatedPerson": _modeled(
        "app.models.related_person",
        "RelatedPersonModel",
        "related_person_id",
        "app.repository.related_person.search",
        "related_person_search",
    ),
    "Organization": _modeled(
        "app.models.organization",
        "OrganizationModel",
        "organization_id",
        "app.repository.organization.search",
        "organization_search",
    ),
    "HealthcareService": _modeled(
        "app.models.healthcare_service",
        "HealthcareServiceModel",
        "healthcare_service_id",
        "app.repository.healthcare_service.search",
        "healthcare_service_search",
    ),
    "Encounter": _modeled(
        "app.models.encounter",
        "EncounterModel",
        "encounter_id",
        "app.repository.encounter.search",
        "encounter_search",
    ),
    "Location": _modeled(
        "app.models.location",
        "LocationModel",
        "location_id",
        "app.repository.location.search",
        "location_search",
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
        select(literal(1)).where(model.service_request_pk == P.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.service_request_pk == P.id, *conditions)
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
    return P.service_request_id == int(token.code)


def _enum_param(column, enum, system: str):
    """(match, present, sort) for a `code` held in an Enum column: `code` or
    `system|code`; another system or `|code` (no system) never matches; an unknown code
    matches nothing (rather than failing the Postgres enum cast)."""

    def match(value, modifier, ctx):
        token = parse_token(value)
        if token.system is not None and token.system != system:
            return false()
        if token.code is None:
            return column.is_not(None)
        try:
            return column == enum(token.code)
        except ValueError:
            return false()

    return match, lambda ctx: column.is_not(None), lambda: column


def _requisition_match(value, modifier, ctx):
    return token_match(P.requisition_system, P.requisition_value, value)


def _occurrence_match(value, modifier, ctx):
    # ServiceRequest.occurrence[x] as a dateTime, a Period or a Timing: matched as a range.
    return period_match(P.occurrence_start, P.occurrence_end, value)


def _authored_match(value, modifier, ctx):
    return period_match(P.authored_start, P.authored_end, value)


# ── identifier / the token parameters ──────────────────────────────────


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


# ── references held as columns: subject / patient / encounter / requester ────


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*`
    columns on the service_request row. `narrowed` restricts a multi-target element to
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


# ── references held in the reference table: based-on / replaces / specimen ──


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
    `requester`): the rows of `resource_type` these service_requests point at."""

    async def fetch(session, ctx, service_requests):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(p, id_)
            for p in service_requests
            if getattr(p, type_) == resource_type and getattr(p, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_child(model, resource_type: str, *conditions):
    """_include of a reference held in a child table (performer, part-of,
    reason-reference)."""

    async def fetch(session, ctx, service_requests):
        ids = select(model.reference_id).where(
            model.service_request_pk.in_({p.id for p in service_requests}),
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


def revinclude_service_requests_via_column(prefix: str, resource_type: str, key):
    """_revinclude=ServiceRequest:subject / :patient / :encounter / :requester —
    service requests whose column reference points at one of these rows (matched on the
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


def revinclude_service_requests_via_child(model, resource_type: str, key, *conditions):
    """_revinclude=ServiceRequest:performer / :based-on / :replaces / :specimen —
    service requests with a row in `model` pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(model.service_request_pk).where(
            model.reference_type == resource_type,
            model.reference_id.in_(ids),
            *conditions,
        )
        return await _fetch(
            session, select(P).where(P.tenant_id == ctx.tenant_id, P.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders ServiceRequest rows."""
    from app.fhir.mappers.service_request import to_fhir_service_request
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "ServiceRequest",
            lambda p: p.service_request_id,
            to_fhir_service_request,
            "service-requests",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def service_request_search() -> SearchRegistry:
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

    def enum_token(name, description, expression, column, enum, system, example):
        match, present, sort = _enum_param(column, enum, system)
        return SearchParam(
            name,
            "token",
            description,
            expression,
            match,
            present,
            frozenset({"not", "missing"}),
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
            "Logical id of the resource (the public service request id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.service_request_id,
            example="80001",
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
            "authored",
            "date",
            "Date request signed",
            "ServiceRequest.authoredOn",
            _authored_match,
            lambda ctx: P.authored_start.is_not(None),
            sort=lambda: P.authored_start,
            example="ge2026-01-01",
        ),
        reference(
            "based-on",
            "What request fulfills",
            "ServiceRequest.basedOn",
            "ServiceRequest/80001",
        ),
        token(
            "body-site",
            "Where procedure is going to be done",
            "ServiceRequest.bodySite",
            "http://snomed.info/sct|368208006",
        ),
        token(
            "category",
            "Classification of service",
            "ServiceRequest.category",
            "http://snomed.info/sct|108252007",
        ),
        token(
            "code",
            "What is being requested/ordered",
            "ServiceRequest.code",
            "http://loinc.org|58410-2",
        ),
        column_ref(
            "encounter",
            "An encounter in which this request is made",
            "ServiceRequest.encounter",
            "encounter",
            ("Encounter",),
            "Encounter/20001",
        ),
        SearchParam(
            "identifier",
            "token",
            "Identifiers assigned to this order",
            "ServiceRequest.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:orders|SR-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "instantiates-canonical",
            "reference",
            "Instantiates FHIR protocol or definition (a canonical URL)",
            "ServiceRequest.instantiatesCanonical",
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
            "ServiceRequest.instantiatesUri",
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
        enum_token(
            "intent",
            "proposal | plan | directive | order | original-order | reflex-order | filler-order | "
            f"instance-order | option (system {_INTENT_SYSTEM})",
            "ServiceRequest.intent",
            P.intent,
            ServiceRequestIntent,
            _INTENT_SYSTEM,
            "order",
        ),
        SearchParam(
            "occurrence",
            "date",
            "When service should occur (a dateTime, a Period or a Timing)",
            "ServiceRequest.occurrence",
            _occurrence_match,
            lambda ctx: or_(
                P.occurrence_start.is_not(None), P.occurrence_end.is_not(None)
            ),
            sort=lambda: P.occurrence_start,
            example="ge2026-01-01",
        ),
        column_ref(
            "patient",
            "Search by subject - a patient",
            "ServiceRequest.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        SearchParam(
            "performer",
            "reference",
            "Requested performer",
            "ServiceRequest.performer",
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
            "performer-type",
            "Performer role",
            "ServiceRequest.performerType",
            "http://snomed.info/sct|309343006",
        ),
        enum_token(
            "priority",
            f"routine | urgent | asap | stat (system {_PRIORITY_SYSTEM})",
            "ServiceRequest.priority",
            P.priority,
            ServiceRequestPriority,
            _PRIORITY_SYSTEM,
            "routine",
        ),
        reference(
            "replaces",
            "What request replaces",
            "ServiceRequest.replaces",
            "ServiceRequest/80001",
        ),
        column_ref(
            "requester",
            "Who/what is requesting service",
            "ServiceRequest.requester",
            "requester",
            REQUESTER_TYPES,
            "Practitioner/30001",
        ),
        SearchParam(
            "requisition",
            "token",
            "Composite Request ID",
            "ServiceRequest.requisition",
            _requisition_match,
            lambda ctx: P.requisition_value.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.requisition_value,
            example="urn:requisitions|RQ-1",
        ),
        reference(
            "specimen",
            "Specimen to be tested",
            "ServiceRequest.specimen",
            "Specimen/310001",
        ),
        enum_token(
            "status",
            "draft | active | on-hold | revoked | completed | entered-in-error | unknown "
            f"(system {_STATUS_SYSTEM})",
            "ServiceRequest.status",
            P.status,
            ServiceRequestStatus,
            _STATUS_SYSTEM,
            "active",
        ),
        column_ref(
            "subject",
            "Search by subject",
            "ServiceRequest.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
    ]

    performer_includes = tuple(
        IncludeTarget("ServiceRequest", "performer", t, _include_child(_Pf, t))
        for t in modeled_performers
    )
    based_on_includes = (
        IncludeTarget(
            "ServiceRequest",
            "based-on",
            "ServiceRequest",
            _include_child(_R, "ServiceRequest", _R.param == "based-on"),
        ),
    )
    replaces_includes = (
        IncludeTarget(
            "ServiceRequest",
            "replaces",
            "ServiceRequest",
            _include_child(_R, "ServiceRequest", _R.param == "replaces"),
        ),
    )
    specimen_includes = (
        IncludeTarget(
            "ServiceRequest",
            "specimen",
            "Specimen",
            _include_child(_R, "Specimen", _R.param == "specimen"),
        ),
    )
    requester_includes = tuple(
        IncludeTarget(
            "ServiceRequest",
            "requester",
            t,
            _include_column("requester", t),
        )
        for t in REQUESTER_TYPES
        if t in _MODELED
    )
    subject_includes = tuple(
        IncludeTarget("ServiceRequest", "subject", t, _include_column("subject", t))
        for t in SUBJECT_TYPES
        if t in _MODELED
    )

    return SearchRegistry(
        resource_type="ServiceRequest",
        params={p.name: p for p in params},
        # Σ elements in the R4 ServiceRequest definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "instantiatesCanonical",
                "instantiatesUri",
                "basedOn",
                "replaces",
                "requisition",
                "status",
                "intent",
                "category",
                "priority",
                "doNotPerform",
                "code",
                "orderDetail",
                "quantityQuantity",
                "quantityRatio",
                "quantityRange",
                "subject",
                "encounter",
                "occurrenceDateTime",
                "occurrencePeriod",
                "occurrenceTiming",
                "asNeededBoolean",
                "asNeededCodeableConcept",
                "authoredOn",
                "requester",
                "performerType",
                "performer",
                "locationCode",
                "locationReference",
                "reasonCode",
                "reasonReference",
                "specimen",
                "bodySite",
                "patientInstruction",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "intent", "subject"}),
        includes=(
            IncludeTarget(
                "ServiceRequest",
                "patient",
                "Patient",
                _include_column("subject", "Patient"),
            ),
            *subject_includes,
            IncludeTarget(
                "ServiceRequest",
                "encounter",
                "Encounter",
                _include_column("encounter", "Encounter"),
            ),
            *requester_includes,
            *performer_includes,
            *based_on_includes,
            *replaces_includes,
            *specimen_includes,
        ),
        # Other resources that point at a ServiceRequest, and a ServiceRequest that is
        # based on / replaces another one pointing back at it.
        revincludes=(
            *reference_observation_revincludes(
                "based-on", "ServiceRequest", lambda p: p.service_request_id
            ),
            *reference_report_revincludes(
                "based-on", "ServiceRequest", lambda p: p.service_request_id
            ),
            *reference_encounter_revincludes(
                "ServiceRequest", lambda p: p.service_request_id, ("based-on",)
            ),
            *based_on_procedure_revincludes(
                "ServiceRequest", lambda p: p.service_request_id
            ),
            IncludeTarget(
                "ServiceRequest",
                "based-on",
                "ServiceRequest",
                revinclude_service_requests_via_child(
                    _R,
                    "ServiceRequest",
                    lambda p: p.service_request_id,
                    _R.param == "based-on",
                ),
                reverse=True,
            ),
            IncludeTarget(
                "ServiceRequest",
                "replaces",
                "ServiceRequest",
                revinclude_service_requests_via_child(
                    _R,
                    "ServiceRequest",
                    lambda p: p.service_request_id,
                    _R.param == "replaces",
                ),
                reverse=True,
            ),
        ),
        default_sort=lambda: [P.service_request_id.desc()],
    )
