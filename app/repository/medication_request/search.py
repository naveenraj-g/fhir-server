"""
FHIR R4 MedicationRequest search parameters
(https://www.hl7.org/fhir/R4/medicationrequest.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
medication_request_search() below. Same arrangement as
app.repository.service_request.search (references held as columns, shared token table).

Each parameter's SQL reads only the search index (MedicationRequestModel's columns and child
tables, see its docstring) - never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.repository._medication_dispense_revinclude import reference_medication_dispense_revincludes
from app.repository._medication_administration_revinclude import column_medication_administration_revincludes
from app.repository._care_plan_revinclude import activity_care_plan_revincludes
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
from app.models.medication_request import (
    DISPENSER_TYPES,
    MEDICATION_TYPES,
    PERFORMER_TYPES,
    REQUESTER_TYPES,
    SUBJECT_TYPES,
    MedicationRequestIdentifier,
    MedicationRequestIntent,
    MedicationRequestModel,
    MedicationRequestPriority,
    MedicationRequestStatus,
    MedicationRequestTiming,
    MedicationRequestToken,
)

P = MedicationRequestModel
_I = MedicationRequestIdentifier
_Tk = MedicationRequestToken
_Tm = MedicationRequestTiming
_STATUS_SYSTEM = "http://hl7.org/fhir/CodeSystem/medicationrequest-status"
_INTENT_SYSTEM = "http://hl7.org/fhir/CodeSystem/medicationrequest-intent"
_PRIORITY_SYSTEM = "http://hl7.org/fhir/request-priority"


def _modeled(module: str, cls: str, id_col: str, search_module: str, factory: str):
    return (module, cls, id_col, search_module, factory)


# Reference targets that are searchable resources on this server: the model to join for
# chaining / `_include`, and its registry.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = {
    "CareTeam": (
        "app.models.care_team",
        "CareTeamModel",
        "care_team_id",
        "app.repository.care_team.search",
        "care_team_search",
    ),
    "Medication": _modeled(
        "app.models.medication",
        "MedicationModel",
        "medication_id",
        "app.repository.medication.search",
        "medication_search",
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
    "Encounter": _modeled(
        "app.models.encounter",
        "EncounterModel",
        "encounter_id",
        "app.repository.encounter.search",
        "encounter_search",
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
        select(literal(1)).where(model.medication_request_pk == P.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.medication_request_pk == P.id, *conditions)
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
    return P.medication_request_id == int(token.code)


def _enum_param(column, enum, system: str):
    """(match, present, sort) for a `code` held in an Enum column: `code` or `system|code`;
    another system or `|code` (no system) never matches; an unknown code matches nothing
    (rather than failing the Postgres enum cast)."""

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


def _authored_match(value, modifier, ctx):
    return period_match(P.authored_start, P.authored_end, value)


def _date_match(value, modifier, ctx):
    # MedicationRequest.dosageInstruction.timing.event: any event of any dosage instruction.
    return _exists(_Tm, period_match(_Tm.event_start, _Tm.event_end, value))


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
    """(match, present, sort) for one of the token parameters held in the shared token
    table, selected by its `param` value."""

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


# -- references held as columns --------------------------------------------------------------


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    medication_request row. `narrowed` restricts a multi-target element to one type
    (`patient` is `subject` resolved to a Patient)."""
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


def _include_column(prefix: str, resource_type: str):
    """_include of a reference held as columns: the rows of `resource_type` these medication
    requests point at."""

    async def fetch(session, ctx, medication_requests):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(m, id_)
            for m in medication_requests
            if getattr(m, type_) == resource_type and getattr(m, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def revinclude_medication_requests_via_column(prefix: str, resource_type: str, key):
    """_revinclude=MedicationRequest:subject / :patient / :encounter / :requester /
    :intended-performer / :medication / :intended-dispenser - medication requests whose column
    reference points at one of these rows (matched on the public id `key(row)`). Declared on
    the registry of each target type."""

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


def _register_kind() -> None:
    """How the search engine identifies and renders MedicationRequest rows."""
    from app.fhir.mappers.medication_request import to_fhir_medication_request
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "MedicationRequest",
            lambda m: m.medication_request_id,
            to_fhir_medication_request,
            "medication-requests",
        )
    )


# -- registry ------------------------------------------------------------------------------

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def medication_request_search() -> SearchRegistry:
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

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public medication request id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.medication_request_id,
            example="90001",
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
            "authoredon",
            "date",
            "Return prescriptions written on this date",
            "MedicationRequest.authoredOn",
            _authored_match,
            lambda ctx: P.authored_start.is_not(None),
            sort=lambda: P.authored_start,
            example="ge2026-01-01",
        ),
        token(
            "category",
            "Returns prescriptions with different categories",
            "MedicationRequest.category",
            "http://terminology.hl7.org/CodeSystem/medicationrequest-category|outpatient",
        ),
        token(
            "code",
            "Return prescriptions of this medication code",
            "(MedicationRequest.medication as CodeableConcept)",
            "http://www.nlm.nih.gov/research/umls/rxnorm|1049502",
        ),
        SearchParam(
            "date",
            "date",
            "Returns medication request to be administered on a specific date",
            "MedicationRequest.dosageInstruction.timing.event",
            _date_match,
            lambda ctx: _exists(_Tm),
            sort=lambda: _child_sort(_Tm.event_start, _Tm),
            example="ge2026-01-01",
        ),
        column_ref(
            "encounter",
            "Return prescriptions with this encounter identifier",
            "MedicationRequest.encounter",
            "encounter",
            ("Encounter",),
            "Encounter/20001",
        ),
        SearchParam(
            "identifier",
            "token",
            "Return prescriptions with this external identifier",
            "MedicationRequest.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:prescriptions|RX-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        column_ref(
            "intended-dispenser",
            "Returns prescriptions intended to be dispensed by this Organization",
            "MedicationRequest.dispenseRequest.performer",
            "dispenser",
            DISPENSER_TYPES,
            "Organization/190001",
        ),
        column_ref(
            "intended-performer",
            "Returns the intended performer of the administration of the medication request",
            "MedicationRequest.performer",
            "performer",
            PERFORMER_TYPES,
            "Practitioner/30001",
        ),
        token(
            "intended-performertype",
            "Returns requests for a specific type of performer",
            "MedicationRequest.performerType",
            "http://snomed.info/sct|309343006",
        ),
        enum_token(
            "intent",
            "proposal | plan | order | original-order | reflex-order | filler-order | "
            f"instance-order | option (system {_INTENT_SYSTEM})",
            "MedicationRequest.intent",
            P.intent,
            MedicationRequestIntent,
            _INTENT_SYSTEM,
            "order",
        ),
        column_ref(
            "medication",
            "Return prescriptions for this medication reference",
            "(MedicationRequest.medication as Reference)",
            "medication",
            MEDICATION_TYPES,
            "Medication/250001",
        ),
        column_ref(
            "patient",
            "Returns prescriptions for a specific patient",
            "MedicationRequest.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        enum_token(
            "priority",
            f"routine | urgent | asap | stat (system {_PRIORITY_SYSTEM})",
            "MedicationRequest.priority",
            P.priority,
            MedicationRequestPriority,
            _PRIORITY_SYSTEM,
            "routine",
        ),
        column_ref(
            "requester",
            "Returns prescriptions prescribed by this prescriber",
            "MedicationRequest.requester",
            "requester",
            REQUESTER_TYPES,
            "Practitioner/30001",
        ),
        enum_token(
            "status",
            "active | on-hold | cancelled | completed | entered-in-error | stopped | draft | unknown "
            f"(system {_STATUS_SYSTEM})",
            "MedicationRequest.status",
            P.status,
            MedicationRequestStatus,
            _STATUS_SYSTEM,
            "active",
        ),
        column_ref(
            "subject",
            "The identity of a patient to list orders for",
            "MedicationRequest.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
    ]

    def includes_for(name, prefix, targets):
        return tuple(
            IncludeTarget("MedicationRequest", name, t, _include_column(prefix, t))
            for t in targets
            if t in _MODELED
        )

    return SearchRegistry(
        resource_type="MedicationRequest",
        params={p.name: p for p in params},
        # Σ elements in the R4 MedicationRequest definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "status",
                "intent",
                "priority",
                "doNotPerform",
                "reportedBoolean",
                "reportedReference",
                "medicationCodeableConcept",
                "medicationReference",
                "subject",
                "authoredOn",
                "requester",
                "performerType",
                "instantiatesCanonical",
                "instantiatesUri",
                "basedOn",
                "groupIdentifier",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset(
            {
                "status",
                "intent",
                "medicationCodeableConcept",
                "medicationReference",
                "subject",
            }
        ),
        includes=(
            IncludeTarget(
                "MedicationRequest",
                "patient",
                "Patient",
                _include_column("subject", "Patient"),
            ),
            *includes_for("subject", "subject", SUBJECT_TYPES),
            *includes_for("encounter", "encounter", ("Encounter",)),
            *includes_for("requester", "requester", REQUESTER_TYPES),
            *includes_for("intended-performer", "performer", PERFORMER_TYPES),
            *includes_for("intended-dispenser", "dispenser", DISPENSER_TYPES),
            *includes_for("medication", "medication", MEDICATION_TYPES),
        ),
        # A MedicationRequest is pointed at by other MedicationRequests (priorPrescription is
        # unindexed; basedOn is not searched), so there is no revinclude of its own.
        revincludes=(
            *reference_medication_dispense_revincludes(
                'prescription', 'MedicationRequest', lambda x: x.medication_request_id
            ),
            *column_medication_administration_revincludes(
                ('request',), 'request', 'MedicationRequest', lambda x: x.medication_request_id
            ),
            *activity_care_plan_revincludes(
                "MedicationRequest", lambda x: x.medication_request_id
            ),
        ),
        default_sort=lambda: [P.medication_request_id.desc()],
    )
