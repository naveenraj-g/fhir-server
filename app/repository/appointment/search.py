"""
FHIR R4 Appointment search parameters
(https://www.hl7.org/fhir/R4/appointment.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
appointment_search() below. Same arrangement as app.repository.patient.search
(multi-target references held in a `param`-keyed table) and
app.repository.schedule.search (actor).

Each parameter's SQL reads only the search index (AppointmentModel's columns
and child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    coded_token_match,
    date_match,
    reference_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.repository._care_plan_revinclude import activity_care_plan_revincludes
from app.repository._appointment_response_revinclude import (
    appointment_response_revincludes,
)
from app.repository._encounter_revinclude import appointment_encounter_revincludes
from app.models.appointment import (
    AppointmentParticipantStatus,
    ACTOR_TYPES,
    REFERENCE_TYPES,
    AppointmentIdentifier,
    AppointmentModel,
    AppointmentParticipant,
    AppointmentReference,
    AppointmentStatus,
    AppointmentToken,
)

A = AppointmentModel
_I = AppointmentIdentifier
_Tk = AppointmentToken
_P = AppointmentParticipant
_R = AppointmentReference
_STATUS_SYSTEM = "http://hl7.org/fhir/appointmentstatus"
_PARTICIPATION_STATUS_SYSTEM = "http://hl7.org/fhir/participationstatus"

# Reference(Any): `supporting-info` can name any type, but the parser only
# accepts `:Type` for a declared target, so list the types a supporting
# document can realistically be. A relative reference to a type not listed is
# still indexed (and found by its absolute URL).
SUPPORTING_INFO_TYPES = (
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Location",
    "HealthcareService",
    "Encounter",
    "Appointment",
    "Slot",
    "Schedule",
    "Condition",
    "Observation",
    "Procedure",
    "DiagnosticReport",
    "DocumentReference",
    "ServiceRequest",
    "MedicationRequest",
    "CarePlan",
    "AllergyIntolerance",
    "Immunization",
    "Questionnaire",
    "QuestionnaireResponse",
    "Task",
)

# Actor / reference types that are searchable resources on this server: the
# model to join for chaining / `_include`, and its registry.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = {
    "ServiceRequest": (
        "app.models.service_request",
        "ServiceRequestModel",
        "service_request_id",
        "app.repository.service_request.search",
        "service_request_search",
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
    "RelatedPerson": (
        "app.models.related_person",
        "RelatedPersonModel",
        "related_person_id",
        "app.repository.related_person.search",
        "related_person_search",
    ),
    "HealthcareService": (
        "app.models.healthcare_service",
        "HealthcareServiceModel",
        "healthcare_service_id",
        "app.repository.healthcare_service.search",
        "healthcare_service_search",
    ),
    "Location": (
        "app.models.location",
        "LocationModel",
        "location_id",
        "app.repository.location.search",
        "location_search",
    ),
    "Slot": (
        "app.models.slot",
        "SlotModel",
        "slot_id",
        "app.repository.slot.search",
        "slot_search",
    ),
    "Condition": (
        "app.models.condition",
        "ConditionModel",
        "condition_id",
        "app.repository.condition.search",
        "condition_search",
    ),
    "Procedure": (
        "app.models.procedure",
        "ProcedureModel",
        "procedure_id",
        "app.repository.procedure.search",
        "procedure_search",
    ),
    "Observation": (
        "app.models.observation",
        "ObservationModel",
        "observation_id",
        "app.repository.observation.search",
        "observation_search",
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
    return exists(select(literal(1)).where(model.appointment_pk == A.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.appointment_pk == A.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(A.updated_at, A.created_at)


# ── _id / status / date ──────────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return A.appointment_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to one code system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an
    unknown code matches nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return A.status.is_not(None)
    try:
        return A.status == AppointmentStatus(token.code)
    except ValueError:
        return false()


def _date_match(value, modifier, ctx):
    # Appointment.start is an instant: matched as a point in time (see date_match).
    return date_match(A.start, value)


# ── identifier / the five CodeableConcept token parameters ───────────────────


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


# ── participants: actor / patient / practitioner / location / part-status ────


def _participant_param(targets: tuple[str, ...]):
    """(match, present, chain, sort) for `actor` (all seven types) or one of
    its narrowed forms (`patient`, `practitioner`, `location` — the actor
    resolves to that single type). All read the participant table."""
    narrowed = targets[0] if len(targets) == 1 else None
    type_filter = (_P.reference_type == narrowed,) if narrowed else ()

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return _exists(
                _P,
                token_condition(
                    _P.reference_identifier_system,
                    _P.reference_identifier_value,
                    parse_token(value),
                ),
            )
        # `modifier` is a target type (actor:Practitioner=30001) or None; a bare
        # id with several targets is ambiguous and is rejected by
        # reference_target(). reference_type is a plain string here.
        return _exists(
            _P,
            reference_match(
                _P.reference_type,
                _P.reference_id,
                _P.reference_reference,
                value,
                modifier,
                ctx,
                targets,
                str,
            ),
        )

    def present(ctx):
        return _exists(
            _P,
            *type_filter,
            or_(
                _P.reference_reference.is_not(None),
                _P.reference_identifier_value.is_not(None),
            ),
        )

    def chain(target, inner, ctx):
        """`actor:<Type>.<p>=v`: some participant actor of that type (same
        tenant) matches `<p>=v`. The subquery doesn't correlate to the outer
        row — it ranges over the referenced resource."""
        model, id_col = _model(target)
        referenced = (
            select(id_col)
            .where(model.tenant_id == ctx.tenant_id, inner)
            .correlate(None)
        )
        return _exists(_P, _P.reference_type == target, _P.reference_id.in_(referenced))

    def sort():
        return _child_sort(_P.reference_id, _P, *type_filter)

    return match, present, chain, sort


def _part_status_match(value, modifier, ctx):
    """`part-status` is a `code` bound to the participation-status system. Some
    participant has this status; another system or an unknown code matches
    nothing."""
    token = parse_token(value)
    if token.system is not None and token.system != _PARTICIPATION_STATUS_SYSTEM:
        return false()
    if token.code is None:
        return _exists(_P, _P.status.is_not(None))
    try:
        return _exists(_P, _P.status == AppointmentParticipantStatus(token.code))
    except ValueError:
        return false()


# ── based-on / reason-reference / slot / supporting-info ─────────────────────


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
        model, id_col = _model(target)
        referenced = (
            select(id_col)
            .where(model.tenant_id == ctx.tenant_id, inner)
            .correlate(None)
        )
        return _exists(
            _R,
            _R.param == param,
            _R.reference_type == target,
            _R.reference_id.in_(referenced),
        )

    def sort():
        return _child_sort(_R.reference_id, _R, _R.param == param)

    return match, present, chain, sort


# ── _include / _revinclude ───────────────────────────────────────────────────


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


def _include_participants(resource_type: str):
    """_include=Appointment:actor[:Type] (and :patient / :practitioner /
    :location) — the participant actors of one type these appointments point
    at (only types that are resources on this server)."""

    async def fetch(session, ctx, appointments):
        model, id_col = _model(resource_type)
        referenced = select(_P.reference_id).where(
            _P.appointment_pk.in_({a.id for a in appointments}),
            _P.reference_type == resource_type,
            _P.reference_id.is_not(None),
        )
        return await _fetch(
            session,
            select(model).where(
                model.tenant_id == ctx.tenant_id, id_col.in_(referenced)
            ),
        )

    return fetch


async def _include_based_on(session, ctx, appointments):
    """_include=Appointment:based-on - the service requests these appointments fulfil."""
    model, id_col = _model("ServiceRequest")
    referenced = select(_R.reference_id).where(
        _R.appointment_pk.in_({a.id for a in appointments}),
        _R.param == "based-on",
        _R.reference_type == "ServiceRequest",
        _R.reference_id.is_not(None),
    )
    return await _fetch(
        session,
        select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(referenced)),
    )


async def _include_slots(session, ctx, appointments):
    """_include=Appointment:slot — the slots these appointments fill."""
    model, id_col = _model("Slot")
    referenced = select(_R.reference_id).where(
        _R.appointment_pk.in_({a.id for a in appointments}),
        _R.param == "slot",
        _R.reference_type == "Slot",
        _R.reference_id.is_not(None),
    )
    return await _fetch(
        session,
        select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(referenced)),
    )


def _include_reason(resource_type: str):
    """_include=Appointment:reason-reference — the Conditions / Procedures these
    appointments are for."""

    async def fetch(session, ctx, appointments):
        model, id_col = _model(resource_type)
        referenced = select(_R.reference_id).where(
            _R.appointment_pk.in_({a.id for a in appointments}),
            _R.param == "reason-reference",
            _R.reference_type == resource_type,
            _R.reference_id.is_not(None),
        )
        return await _fetch(
            session,
            select(model).where(
                model.tenant_id == ctx.tenant_id, id_col.in_(referenced)
            ),
        )

    return fetch


def revinclude_appointments_via_reason(resource_type: str, key):
    """_revinclude=Appointment:reason-reference — appointments whose reason is one
    of these Conditions / Procedures."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.appointment_pk).where(
            _R.param == "reason-reference",
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(A).where(A.tenant_id == ctx.tenant_id, A.id.in_(pks))
        )

    return fetch


def revinclude_appointments_via_participant(resource_type: str, key):
    """_revinclude=Appointment:actor / :patient / :practitioner / :location —
    appointments with a participant actor of this type pointing at one of
    these rows (matched on the public id `key(row)`). Declared on the registry
    of each actor type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_P.appointment_pk).where(
            _P.reference_type == resource_type, _P.reference_id.in_(ids)
        )
        return await _fetch(
            session, select(A).where(A.tenant_id == ctx.tenant_id, A.id.in_(pks))
        )

    return fetch


def revinclude_appointments_via_slot(key):
    """_revinclude=Appointment:slot — appointments filling one of these slots."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.appointment_pk).where(
            _R.param == "slot", _R.reference_type == "Slot", _R.reference_id.in_(ids)
        )
        return await _fetch(
            session, select(A).where(A.tenant_id == ctx.tenant_id, A.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Appointment rows."""
    from app.fhir.mappers.appointment import to_fhir_appointment
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "Appointment",
            lambda a: a.appointment_id,
            to_fhir_appointment,
            "appointments",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})


@cache
def appointment_search() -> SearchRegistry:
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

    def participant(name, description, expression, targets, example):
        match, present, chain, sort = _participant_param(targets)
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
            modifier_docs={
                "identifier": "`:identifier` — match the logical identifier of a participant that has no resource here."
            },
        )

    def reference(name, description, expression, example, chain_types=()):
        # The R4 search-parameter name is also the `param` value in the reference table.
        targets = REFERENCE_TYPES[name] or SUPPORTING_INFO_TYPES
        match, present, chain, sort = _reference_param(name, targets)
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
            chain_targets={t: _registry_of(t) for t in chain_types},
            sort=sort,
            example=example,
        )

    part_status_description = (
        "The Participation status of the subject, or other participant on the appointment. Can be used to "
        f"locate participants that have not responded to meeting requests (system {_PARTICIPATION_STATUS_SYSTEM})"
    )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public appointment id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: A.appointment_id,
            example="40001",
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
        participant(
            "actor",
            "Any one of the individuals participating in the appointment",
            "Appointment.participant.actor",
            ACTOR_TYPES,
            "Practitioner/30001",
        ),
        token(
            "appointment-type",
            "The style of appointment or patient that has been booked in the slot (not service type)",
            "Appointment.appointmentType",
            "http://terminology.hl7.org/CodeSystem/v2-0276|ROUTINE",
        ),
        reference(
            "based-on",
            "The service request this appointment is allocated to assess",
            "Appointment.basedOn",
            "ServiceRequest/80001",
            chain_types=("ServiceRequest",),
        ),
        SearchParam(
            "date",
            "date",
            "Appointment date/time.",
            "Appointment.start",
            _date_match,
            lambda ctx: A.start.is_not(None),
            sort=lambda: A.start,
            example="ge2026-06-01T09:00:00Z",
        ),
        SearchParam(
            "identifier",
            "token",
            "An Identifier of the Appointment",
            "Appointment.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:appointments|AP-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        participant(
            "location",
            "This location is listed in the participants of the appointment",
            "Appointment.participant.actor.where(resolve() is Location)",
            ("Location",),
            "Location/230001",
        ),
        SearchParam(
            "part-status",
            "token",
            part_status_description,
            "Appointment.participant.status",
            _part_status_match,
            lambda ctx: _exists(_P, _P.status.is_not(None)),
            frozenset({"not", "missing"}),
            sort=lambda: _child_sort(_P.status, _P),
            example="accepted",
        ),
        participant(
            "patient",
            "One of the individuals of the appointment is this patient",
            "Appointment.participant.actor.where(resolve() is Patient)",
            ("Patient",),
            "Patient/10001",
        ),
        participant(
            "practitioner",
            "One of the individuals of the appointment is this practitioner",
            "Appointment.participant.actor.where(resolve() is Practitioner)",
            ("Practitioner",),
            "Practitioner/30001",
        ),
        token(
            "reason-code",
            "Coded reason this appointment is scheduled",
            "Appointment.reasonCode",
            "http://snomed.info/sct|413153004",
        ),
        reference(
            "reason-reference",
            "Reason the appointment is to take place (resource)",
            "Appointment.reasonReference",
            "Condition/120001",
            chain_types=("Condition", "Procedure", "Observation"),
        ),
        token(
            "service-category",
            "A broad categorization of the service that is to be performed during this appointment",
            "Appointment.serviceCategory",
            "http://terminology.hl7.org/CodeSystem/service-category|17",
        ),
        token(
            "service-type",
            "The specific service that is to be performed during this appointment",
            "Appointment.serviceType",
            "http://terminology.hl7.org/CodeSystem/service-type|124",
        ),
        reference(
            "slot",
            "The slots that this appointment is filling",
            "Appointment.slot",
            "Slot/220001",
            chain_types=("Slot",),
        ),
        token(
            "specialty",
            "The specialty of a practitioner that would be required to perform the service requested in this appointment",
            "Appointment.specialty",
            "http://snomed.info/sct|394579002",
        ),
        SearchParam(
            "status",
            "token",
            "The overall status of the appointment (proposed | pending | booked | arrived | fulfilled | cancelled | "
            f"noshow | entered-in-error | checked-in | waitlist; system {_STATUS_SYSTEM})",
            "Appointment.status",
            _status_match,
            lambda ctx: A.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: A.status,
            example="booked",
        ),
        reference(
            "supporting-info",
            "Additional information to support the appointment",
            "Appointment.supportingInformation",
            "Encounter/20001",
        ),
    ]

    actor_includes = tuple(
        IncludeTarget("Appointment", "actor", t, _include_participants(t))
        for t in _MODELED
        if t not in ("Slot", "Condition", "Procedure", "Observation")
    )
    narrowed_includes = tuple(
        IncludeTarget("Appointment", name, t, _include_participants(t))
        for name, t in (
            ("patient", "Patient"),
            ("practitioner", "Practitioner"),
            ("location", "Location"),
        )
    )

    return SearchRegistry(
        resource_type="Appointment",
        params={p.name: p for p in params},
        # Σ elements in the R4 Appointment definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "status",
                "cancelationReason",
                "serviceCategory",
                "serviceType",
                "specialty",
                "appointmentType",
                "reasonCode",
                "start",
                "end",
                "participant",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "participant"}),
        # One include per target type, so `_include=Appointment:actor` brings in all
        # of them and `Appointment:actor:Location` just the Locations. RelatedPerson /
        # Device, ServiceRequest, Condition, ... aren't rebuilt resources here.
        includes=(
            *actor_includes,
            *narrowed_includes,
            IncludeTarget("Appointment", "slot", "Slot", _include_slots),
            IncludeTarget(
                "Appointment", "based-on", "ServiceRequest", _include_based_on
            ),
            IncludeTarget(
                "Appointment",
                "reason-reference",
                "Condition",
                _include_reason("Condition"),
            ),
            IncludeTarget(
                "Appointment",
                "reason-reference",
                "Procedure",
                _include_reason("Procedure"),
            ),
            IncludeTarget(
                "Appointment",
                "reason-reference",
                "Observation",
                _include_reason("Observation"),
            ),
        ),
        # AppointmentResponse.appointment points here (Encounter, ... add theirs when rebuilt).
        revincludes=(
            *activity_care_plan_revincludes("Appointment", lambda x: x.appointment_id),
            *appointment_response_revincludes(lambda a: a.appointment_id),
            *appointment_encounter_revincludes(lambda a: a.appointment_id),
        ),
        default_sort=lambda: [A.appointment_id.desc()],
    )
