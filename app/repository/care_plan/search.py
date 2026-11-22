"""
FHIR R4 CarePlan search parameters (https://www.hl7.org/fhir/R4/careplan.html#search) plus the
common `_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from care_plan_search() below. Same
arrangement as app.repository.service_request.search (references held as columns, shared token
and reference tables, a performer table, `instantiates-uri` / `instantiates-canonical`), plus an
activity table for `activity-reference` and `activity-date`.

Each parameter's SQL reads only the search index (CarePlanModel's columns and child tables, see
its docstring) - never `content`.
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
from app.repository._diagnostic_report_revinclude import reference_report_revincludes
from app.repository._observation_revinclude import reference_observation_revincludes
from app.repository._procedure_revinclude import based_on_procedure_revincludes
from app.repository._service_request_revinclude import (
    based_on_service_request_revincludes,
)
from app.models.care_plan import (
    ACTIVITY_REFERENCE_TYPES,
    ENCOUNTER_TYPES,
    PERFORMER_TYPES,
    REFERENCE_TYPES,
    SUBJECT_TYPES,
    CarePlanActivity,
    CarePlanIdentifier,
    CarePlanInstantiatesUri,
    CarePlanIntent,
    CarePlanModel,
    CarePlanPerformer,
    CarePlanReference,
    CarePlanStatus,
    CarePlanToken,
)

P = CarePlanModel
_I = CarePlanIdentifier
_Tk = CarePlanToken
_R = CarePlanReference
_Pf = CarePlanPerformer
_U = CarePlanInstantiatesUri
_A = CarePlanActivity
_STATUS_SYSTEM = "http://hl7.org/fhir/request-status"
_INTENT_SYSTEM = "http://hl7.org/fhir/request-intent"
_ABSOLUTE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _modeled(module: str, cls: str, id_col: str, search_module: str, factory: str):
    return (module, cls, id_col, search_module, factory)


# Reference targets that are searchable resources on this server: the model to
# join for chaining / `_include`, and its registry.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = {
    "CarePlan": _modeled(
        "app.models.care_plan",
        "CarePlanModel",
        "care_plan_id",
        "app.repository.care_plan.search",
        "care_plan_search",
    ),
    "CareTeam": _modeled(
        "app.models.care_team",
        "CareTeamModel",
        "care_team_id",
        "app.repository.care_team.search",
        "care_team_search",
    ),
    "Condition": _modeled(
        "app.models.condition",
        "ConditionModel",
        "condition_id",
        "app.repository.condition.search",
        "condition_search",
    ),
    "Appointment": _modeled(
        "app.models.appointment",
        "AppointmentModel",
        "appointment_id",
        "app.repository.appointment.search",
        "appointment_search",
    ),
    "MedicationRequest": _modeled(
        "app.models.medication_request",
        "MedicationRequestModel",
        "medication_request_id",
        "app.repository.medication_request.search",
        "medication_request_search",
    ),
    "ServiceRequest": _modeled(
        "app.models.service_request",
        "ServiceRequestModel",
        "service_request_id",
        "app.repository.service_request.search",
        "service_request_search",
    ),
    "Patient": _modeled(
        "app.models.patient",
        "PatientModel",
        "patient_id",
        "app.repository.patient.search",
        "patient_search",
    ),
    "Group": _modeled(
        "app.models.group",
        "GroupModel",
        "group_id",
        "app.repository.group.search",
        "group_search",
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
    return exists(select(literal(1)).where(model.care_plan_pk == P.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.care_plan_pk == P.id, *conditions)
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
    return P.care_plan_id == int(token.code)


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


def _date_match(value, modifier, ctx):
    # CarePlan.period is a Period: matched as the range it covers (a care plan with no period
    # never matches).
    return period_match(P.period_start, P.period_end, value)


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
    columns on the care_plan row. `narrowed` restricts a multi-target element to
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


# ── activity: activity-reference / activity-date ─────────────────────────────


def _activity_ref_match(value, modifier, ctx):
    if modifier == "identifier":
        return _exists(
            _A,
            token_condition(
                _A.reference_identifier_system,
                _A.reference_identifier_value,
                parse_token(value),
            ),
        )
    return _exists(
        _A,
        reference_match(
            _A.reference_type,
            _A.reference_id,
            _A.reference_reference,
            value,
            modifier,
            ctx,
            ACTIVITY_REFERENCE_TYPES,
            str,
        ),
    )


def _activity_ref_present(ctx):
    return _exists(
        _A,
        or_(
            _A.reference_reference.is_not(None),
            _A.reference_identifier_value.is_not(None),
        ),
    )


def _activity_ref_chain(target, inner, ctx):
    return _exists(
        _A,
        _A.reference_type == target,
        _A.reference_id.in_(_referenced(target, inner, ctx)),
    )


def _activity_date_match(value, modifier, ctx):
    # activity.detail.scheduled[x] as a Period or a Timing: matched as the range it covers.
    return _exists(_A, period_match(_A.scheduled_start, _A.scheduled_end, value))


def _activity_date_present(ctx):
    return _exists(
        _A, or_(_A.scheduled_start.is_not(None), _A.scheduled_end.is_not(None))
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
    `requester`): the rows of `resource_type` these care_plans point at."""

    async def fetch(session, ctx, care_plans):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(p, id_)
            for p in care_plans
            if getattr(p, type_) == resource_type and getattr(p, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_child(model, resource_type: str, *conditions):
    """_include of a reference held in a child table (performer, part-of,
    reason-reference)."""

    async def fetch(session, ctx, care_plans):
        ids = select(model.reference_id).where(
            model.care_plan_pk.in_({p.id for p in care_plans}),
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


def revinclude_care_plans_via_column(prefix: str, resource_type: str, key):
    """_revinclude=CarePlan:subject / :patient / :encounter / :requester —
    care plans whose column reference points at one of these rows (matched on the
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


def revinclude_care_plans_via_child(model, resource_type: str, key, *conditions):
    """_revinclude=CarePlan:performer / :based-on / :replaces / :specimen —
    care plans with a row in `model` pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(model.care_plan_pk).where(
            model.reference_type == resource_type,
            model.reference_id.in_(ids),
            *conditions,
        )
        return await _fetch(
            session, select(P).where(P.tenant_id == ctx.tenant_id, P.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders CarePlan rows."""
    from app.fhir.mappers.care_plan import to_fhir_care_plan
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "CarePlan",
            lambda p: p.care_plan_id,
            to_fhir_care_plan,
            "care-plans",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def care_plan_search() -> SearchRegistry:
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
    modeled_activity_refs = [t for t in ACTIVITY_REFERENCE_TYPES if t in _MODELED]

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public care plan id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.care_plan_id,
            example="290001",
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
            "activity-code",
            "Detail type of activity",
            "CarePlan.activity.detail.code",
            "http://snomed.info/sct|386053000",
        ),
        SearchParam(
            "activity-date",
            "date",
            "Specified date occurs within period specified by CarePlan.activity.detail.scheduled[x]",
            "CarePlan.activity.detail.scheduled",
            _activity_date_match,
            _activity_date_present,
            sort=lambda: _child_sort(_A.scheduled_start, _A),
            example="ge2026-01-01",
        ),
        SearchParam(
            "activity-reference",
            "reference",
            "Activity that is intended to be part of the care plan",
            "CarePlan.activity.reference",
            _activity_ref_match,
            _activity_ref_present,
            _REFERENCE,
            targets=ACTIVITY_REFERENCE_TYPES,
            chain=_activity_ref_chain,
            chain_targets={t: _registry_of(t) for t in modeled_activity_refs},
            sort=lambda: _child_sort(_A.reference_id, _A),
            example="ServiceRequest/80001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        reference(
            "based-on",
            "Fulfills CarePlan",
            "CarePlan.basedOn",
            "CarePlan/290001",
        ),
        reference(
            "care-team",
            "Who's involved in plan?",
            "CarePlan.careTeam",
            "CareTeam/390001",
        ),
        token(
            "category",
            "Type of plan",
            "CarePlan.category",
            "http://hl7.org/fhir/us/core/CodeSystem/careplan-category|assess-plan",
        ),
        reference(
            "condition",
            "Health issues this plan addresses",
            "CarePlan.addresses",
            "Condition/120001",
        ),
        SearchParam(
            "date",
            "date",
            "Time period plan covers",
            "CarePlan.period",
            _date_match,
            lambda ctx: or_(P.period_start.is_not(None), P.period_end.is_not(None)),
            sort=lambda: P.period_start,
            example="ge2026-01-01",
        ),
        column_ref(
            "encounter",
            "The Encounter during which this CarePlan was created",
            "CarePlan.encounter",
            "encounter",
            ENCOUNTER_TYPES,
            "Encounter/20001",
        ),
        reference(
            "goal",
            "Desired outcome of plan",
            "CarePlan.goal",
            "Goal/460001",
        ),
        SearchParam(
            "identifier",
            "token",
            "External Ids for this plan",
            "CarePlan.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:care-plans|CP-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "instantiates-canonical",
            "reference",
            "Instantiates FHIR protocol or definition (a canonical URL)",
            "CarePlan.instantiatesCanonical",
            canonical_match,
            canonical_present,
            frozenset({"missing"}),
            targets=REFERENCE_TYPES["instantiates-canonical"],
            sort=canonical_sort,
            example="http://example.org/fhir/PlanDefinition/diabetes",
            modifier_docs={
                "missing": "`:missing=true` — resources with no canonical for this parameter; `:missing=false` — resources that have one."
            },
        ),
        SearchParam(
            "instantiates-uri",
            "uri",
            "Instantiates external protocol or definition",
            "CarePlan.instantiatesUri",
            _uri_match,
            lambda ctx: _exists(_U),
            frozenset({"above", "below", "missing"}),
            sort=lambda: _child_sort(_U.uri, _U),
            example="http://example.org/protocols/diabetes",
            modifier_docs={
                "below": "`:below` — stored URIs that start with the value (`http://acme.org/p` finds `http://acme.org/p/1`).",
                "above": "`:above` — stored URIs that are a prefix of the value.",
            },
        ),
        enum_token(
            "intent",
            f"proposal | plan | order | option (system {_INTENT_SYSTEM})",
            "CarePlan.intent",
            P.intent,
            CarePlanIntent,
            _INTENT_SYSTEM,
            "plan",
        ),
        reference(
            "part-of",
            "Part of referenced CarePlan",
            "CarePlan.partOf",
            "CarePlan/290001",
        ),
        column_ref(
            "patient",
            "Who the care plan is for",
            "CarePlan.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        SearchParam(
            "performer",
            "reference",
            "Matches if the practitioner is listed as a performer in any of the activities",
            "CarePlan.activity.detail.performer",
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
        reference(
            "replaces",
            "CarePlan replaced by this CarePlan",
            "CarePlan.replaces",
            "CarePlan/290001",
        ),
        enum_token(
            "status",
            "draft | active | on-hold | revoked | completed | entered-in-error | unknown "
            f"(system {_STATUS_SYSTEM})",
            "CarePlan.status",
            P.status,
            CarePlanStatus,
            _STATUS_SYSTEM,
            "active",
        ),
        column_ref(
            "subject",
            "Who the care plan is for",
            "CarePlan.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
    ]

    subject_includes = tuple(
        IncludeTarget("CarePlan", "subject", t, _include_column("subject", t))
        for t in SUBJECT_TYPES
    )
    performer_includes = tuple(
        IncludeTarget("CarePlan", "performer", t, _include_child(_Pf, t))
        for t in modeled_performers
    )
    activity_includes = tuple(
        IncludeTarget("CarePlan", "activity-reference", t, _include_child(_A, t))
        for t in modeled_activity_refs
    )

    def reference_include(param: str, target: str):
        return IncludeTarget(
            "CarePlan",
            param,
            target,
            _include_child(_R, target, _R.param == param),
        )

    def self_revinclude(param: str):
        return IncludeTarget(
            "CarePlan",
            param,
            "CarePlan",
            revinclude_care_plans_via_child(
                _R, "CarePlan", lambda p: p.care_plan_id, _R.param == param
            ),
            reverse=True,
        )

    return SearchRegistry(
        resource_type="CarePlan",
        params={p.name: p for p in params},
        # Σ elements in the R4 CarePlan definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "instantiatesCanonical",
                "instantiatesUri",
                "basedOn",
                "replaces",
                "partOf",
                "status",
                "intent",
                "category",
                "title",
                "description",
                "subject",
                "encounter",
                "period",
                "created",
                "author",
                "addresses",
                "supportingInfo",
                "goal",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "intent", "subject"}),
        includes=(
            IncludeTarget(
                "CarePlan",
                "patient",
                "Patient",
                _include_column("subject", "Patient"),
            ),
            *subject_includes,
            IncludeTarget(
                "CarePlan",
                "encounter",
                "Encounter",
                _include_column("encounter", "Encounter"),
            ),
            reference_include("based-on", "CarePlan"),
            reference_include("replaces", "CarePlan"),
            reference_include("part-of", "CarePlan"),
            reference_include("care-team", "CareTeam"),
            reference_include("condition", "Condition"),
            *performer_includes,
            *activity_includes,
        ),
        # Other resources that point at a CarePlan are not rebuilt/wired yet; a CarePlan that is
        # based on / replaces / part of another one points back at it.
        revincludes=(
            *reference_observation_revincludes(
                "based-on", "CarePlan", lambda x: x.care_plan_id
            ),
            *reference_report_revincludes(
                "based-on", "CarePlan", lambda x: x.care_plan_id
            ),
            *based_on_procedure_revincludes("CarePlan", lambda x: x.care_plan_id),
            *based_on_service_request_revincludes("CarePlan", lambda x: x.care_plan_id),
            self_revinclude("based-on"),
            self_revinclude("replaces"),
            self_revinclude("part-of"),
        ),
        default_sort=lambda: [P.care_plan_id.desc()],
    )
