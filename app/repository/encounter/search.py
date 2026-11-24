"""
FHIR R4 Encounter search parameters
(https://www.hl7.org/fhir/R4/encounter.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
encounter_search() below. Same arrangement as app.repository.appointment.search
(participants, token and reference tables) and app.repository.appointment_response.search
(references held as columns on the row); `length` is the engine's first
`quantity` search (app.fhir.search.quantity).

Each parameter's SQL reads only the search index (EncounterModel's columns and
child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.repository._communication_revinclude import column_communication_revincludes
from app.repository._flag_revinclude import column_flag_revincludes
from app.repository._task_revinclude import column_task_revincludes
from app.repository._search_targets import MODELED
from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.repository._medication_dispense_revinclude import (
    column_medication_dispense_revincludes,
)
from app.repository._medication_administration_revinclude import (
    column_medication_administration_revincludes,
)
from app.repository._medication_statement_revinclude import (
    column_medication_statement_revincludes,
)
from app.repository._questionnaire_response_revinclude import (
    column_questionnaire_response_revincludes,
)
from app.repository._document_reference_revinclude import (
    reference_document_reference_revincludes,
)
from app.repository._care_plan_revinclude import column_care_plan_revincludes
from app.repository._care_team_revinclude import column_care_team_revincludes
from app.repository._medication_request_revinclude import (
    column_medication_request_revincludes,
)
from app.repository._service_request_revinclude import (
    column_service_request_revincludes,
    performer_service_request_revincludes,
    specimen_service_request_revincludes,
)
from app.repository._clinical_impression_revinclude import column_impression_revincludes
from app.repository._risk_assessment_revinclude import column_risk_revincludes
from app.repository._observation_revinclude import column_observation_revincludes
from app.repository._condition_revinclude import encounter_condition_revincludes
from app.repository._procedure_revinclude import encounter_procedure_revincludes
from app.repository._diagnostic_report_revinclude import encounter_report_revincludes
from app.fhir.search.quantity import quantity_match
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
from app.models.encounter import (
    PARTICIPANT_TYPES,
    REFERENCE_TYPES,
    SUBJECT_TYPES,
    EncounterIdentifier,
    EncounterLocation,
    EncounterModel,
    EncounterParticipant,
    EncounterReference,
    EncounterStatus,
    EncounterToken,
)

E = EncounterModel
_I = EncounterIdentifier
_Tk = EncounterToken
_R = EncounterReference
_P = EncounterParticipant
_L = EncounterLocation
_STATUS_SYSTEM = "http://hl7.org/fhir/encounter-status"

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
    return exists(select(literal(1)).where(model.encounter_pk == E.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.encounter_pk == E.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(E.updated_at, E.created_at)


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition. Does
    not correlate to the outer row — it ranges over the referenced resource."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


# ── _id / status / class / date / length ─────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return E.encounter_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to one code system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an
    unknown code matches nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return E.status.is_not(None)
    try:
        return E.status == EncounterStatus(token.code)
    except ValueError:
        return false()


def _class_match(value, modifier, ctx):
    # Encounter.class is a bare Coding: `:text` matches its display.
    return coded_token_match(
        E.class_system, E.class_code, value, modifier, (E.class_display_norm,)
    )


def _date_match(value, modifier, ctx):
    # Encounter.period is a Period: matched as a range (see period_match).
    return period_match(E.period_start, E.period_end, value)


def _length_match(value, modifier, ctx):
    return quantity_match(
        E.length_value, E.length_system, E.length_code, E.length_unit, value
    )


# ── identifier / the four CodeableConcept token parameters ───────────────────


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


# ── references held as columns: subject / patient / part-of / service-provider ──


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*`
    columns on the encounter row. `narrowed` restricts a multi-target element to
    one type (`patient` is `subject` resolved to a Patient)."""
    ref, type_, id_ = (
        getattr(E, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(E, f"{prefix}_identifier_system"),
        getattr(E, f"{prefix}_identifier_value"),
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


# ── references held in the reference table ───────────────────────────────────


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


# ── participants: participant / practitioner ─────────────────────────────────


def _participant_param(targets: tuple[str, ...]):
    """(match, present, chain, sort) for `participant` (Practitioner |
    PractitionerRole | RelatedPerson) or `practitioner` (the individual
    resolves to a Practitioner). Both read the participant table."""
    narrowed = targets[0] if len(targets) == 1 else None
    type_filter = (_P.reference_type == narrowed,) if narrowed else ()

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return _exists(
                _P,
                *type_filter,
                token_condition(
                    _P.reference_identifier_system,
                    _P.reference_identifier_value,
                    parse_token(value),
                ),
            )
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
        return _exists(
            _P,
            _P.reference_type == target,
            _P.reference_id.in_(_referenced(target, inner, ctx)),
        )

    def sort():
        return _child_sort(_P.reference_id, _P, *type_filter)

    return match, present, chain, sort


# ── locations: location / location-period ────────────────────────────────────


def _location_match(value, modifier, ctx):
    if modifier == "identifier":
        return _exists(
            _L,
            token_condition(
                _L.reference_identifier_system,
                _L.reference_identifier_value,
                parse_token(value),
            ),
        )
    return _exists(
        _L,
        reference_match(
            _L.reference_type,
            _L.reference_id,
            _L.reference_reference,
            value,
            modifier,
            ctx,
            ("Location",),
            str,
        ),
    )


def _location_present(ctx):
    return _exists(
        _L,
        or_(
            _L.reference_reference.is_not(None),
            _L.reference_identifier_value.is_not(None),
        ),
    )


def _location_chain(target, inner, ctx):
    return _exists(
        _L,
        _L.reference_type == "Location",
        _L.reference_id.in_(_referenced("Location", inner, ctx)),
    )


def _location_period_match(value, modifier, ctx):
    return _exists(_L, period_match(_L.period_start, _L.period_end, value))


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
    """_include of a reference held as columns (`subject`, `patient`, `part-of`,
    `service-provider`): the rows of `resource_type` these encounters point at."""

    async def fetch(session, ctx, encounters):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(e, id_)
            for e in encounters
            if getattr(e, type_) == resource_type and getattr(e, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_child(model, resource_type: str, *conditions):
    """_include of a reference held in a child table (appointment, location,
    participant, practitioner)."""

    async def fetch(session, ctx, encounters):
        ids = select(model.reference_id).where(
            model.encounter_pk.in_({e.id for e in encounters}),
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


def revinclude_encounters_via_column(prefix: str, resource_type: str, key):
    """_revinclude=Encounter:subject / :patient / :part-of / :service-provider —
    encounters whose column reference points at one of these rows (matched on
    the public id `key(row)`)."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        type_, id_ = getattr(E, f"{prefix}_type"), getattr(E, f"{prefix}_id")
        return await _fetch(
            session,
            select(E).where(
                E.tenant_id == ctx.tenant_id, type_ == resource_type, id_.in_(ids)
            ),
        )

    return fetch


def revinclude_encounters_via_child(model, resource_type: str, key, *conditions):
    """_revinclude=Encounter:appointment / :location / :participant /
    :practitioner — encounters with a row in `model` pointing at one of these."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(model.encounter_pk).where(
            model.reference_type == resource_type,
            model.reference_id.in_(ids),
            *conditions,
        )
        return await _fetch(
            session, select(E).where(E.tenant_id == ctx.tenant_id, E.id.in_(pks))
        )

    return fetch


def revinclude_encounters_via_appointment(key):
    return revinclude_encounters_via_child(
        _R, "Appointment", key, _R.param == "appointment"
    )


def revinclude_encounters_via_reference(param: str, resource_type: str, key):
    """_revinclude=Encounter:diagnosis / :reason-reference — encounters whose
    `param` reference points at one of these Conditions / Procedures."""
    return revinclude_encounters_via_child(_R, resource_type, key, _R.param == param)


def _register_kind() -> None:
    """How the search engine identifies and renders Encounter rows."""
    from app.fhir.mappers.encounter import to_fhir_encounter
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "Encounter", lambda e: e.encounter_id, to_fhir_encounter, "encounters"
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def encounter_search() -> SearchRegistry:
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

    def reference(name, description, expression, example, chain_types=()):
        # The R4 search-parameter name is also the `param` value in the reference table.
        targets = REFERENCE_TYPES[name]
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
            modifier_docs=_IDENTIFIER_DOC,
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
            modifier_docs=_IDENTIFIER_DOC,
        )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public encounter id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: E.encounter_id,
            example="20001",
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
            "account",
            "The set of accounts that may be used for billing for this Encounter",
            "Encounter.account",
            "Account/1",
        ),
        reference(
            "appointment",
            "The appointment that scheduled this encounter",
            "Encounter.appointment",
            "Appointment/40001",
            chain_types=("Appointment",),
        ),
        reference(
            "based-on",
            "The ServiceRequest that initiated this encounter",
            "Encounter.basedOn",
            "ServiceRequest/80001",
            chain_types=("ServiceRequest",),
        ),
        SearchParam(
            "class",
            "token",
            "Classification of patient encounter",
            "Encounter.class",
            _class_match,
            lambda ctx: or_(E.class_code.is_not(None), E.class_system.is_not(None)),
            _TOKEN,
            sort=lambda: E.class_code,
            example="http://terminology.hl7.org/CodeSystem/v3-ActCode|AMB",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on the Coding's display."
            },
        ),
        SearchParam(
            "date",
            "date",
            "A date within the period the Encounter lasted",
            "Encounter.period",
            _date_match,
            lambda ctx: or_(E.period_start.is_not(None), E.period_end.is_not(None)),
            sort=lambda: E.period_start,
            example="ge2026-06-01",
        ),
        reference(
            "diagnosis",
            "The diagnosis or procedure relevant to the encounter",
            "Encounter.diagnosis.condition",
            "Condition/120001",
            chain_types=("Condition", "Procedure"),
        ),
        reference(
            "episode-of-care",
            "Episode(s) of care that this encounter should be recorded against",
            "Encounter.episodeOfCare",
            "EpisodeOfCare/350001",
            chain_types=("EpisodeOfCare",),
        ),
        SearchParam(
            "identifier",
            "token",
            "Identifier(s) by which this encounter is known",
            "Encounter.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:encounters|E-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "length",
            "quantity",
            "Length of encounter in days (`[prefix]number[|system|code]`; units are compared as written, "
            "with no UCUM conversion)",
            "Encounter.length",
            _length_match,
            lambda ctx: E.length_value.is_not(None),
            sort=lambda: E.length_value,
            example="gt5|http://unitsofmeasure.org|d",
        ),
        SearchParam(
            "location",
            "reference",
            "Location the encounter takes place",
            "Encounter.location.location",
            _location_match,
            _location_present,
            _REFERENCE,
            targets=("Location",),
            chain=_location_chain,
            chain_targets={"Location": _registry_of("Location")},
            sort=lambda: _child_sort(_L.reference_id, _L),
            example="Location/230001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        SearchParam(
            "location-period",
            "date",
            "Time period during which the patient was present at the location",
            "Encounter.location.period",
            _location_period_match,
            lambda ctx: _exists(
                _L, or_(_L.period_start.is_not(None), _L.period_end.is_not(None))
            ),
            sort=lambda: _child_sort(_L.period_start, _L),
            example="ge2026-06-01",
        ),
        column_ref(
            "part-of",
            "Another Encounter this encounter is part of",
            "Encounter.partOf",
            "part_of",
            ("Encounter",),
            "Encounter/20001",
        ),
        participant(
            "participant",
            "Persons involved in the encounter other than the patient",
            "Encounter.participant.individual",
            PARTICIPANT_TYPES,
            "Practitioner/30001",
        ),
        token(
            "participant-type",
            "Role of participant in encounter",
            "Encounter.participant.type",
            "http://terminology.hl7.org/CodeSystem/v3-ParticipationType|ATND",
        ),
        column_ref(
            "patient",
            "The patient present at the encounter",
            "Encounter.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        participant(
            "practitioner",
            "Persons involved in the encounter other than the patient",
            "Encounter.participant.individual.where(resolve() is Practitioner)",
            ("Practitioner",),
            "Practitioner/30001",
        ),
        token(
            "reason-code",
            "Coded reason the encounter takes place",
            "Encounter.reasonCode",
            "http://snomed.info/sct|185347001",
        ),
        reference(
            "reason-reference",
            "Reason the encounter takes place (reference)",
            "Encounter.reasonReference",
            "Condition/120001",
            chain_types=("Condition", "Procedure", "Observation"),
        ),
        column_ref(
            "service-provider",
            "The organization (facility) responsible for this encounter",
            "Encounter.serviceProvider",
            "service_provider",
            ("Organization",),
            "Organization/190001",
        ),
        token(
            "special-arrangement",
            "Wheelchair, translator, stretcher, etc.",
            "Encounter.hospitalization.specialArrangement",
            "http://terminology.hl7.org/CodeSystem/v3-EncounterSpecialCourtesy|wheel",
        ),
        SearchParam(
            "status",
            "token",
            "planned | arrived | triaged | in-progress | onleave | finished | cancelled | entered-in-error | "
            f"unknown (system {_STATUS_SYSTEM})",
            "Encounter.status",
            _status_match,
            lambda ctx: E.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: E.status,
            example="in-progress",
        ),
        column_ref(
            "subject",
            "The patient or group present at the encounter",
            "Encounter.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
        token(
            "type",
            "Specific type of encounter",
            "Encounter.type",
            "http://snomed.info/sct|270427003",
        ),
    ]

    participant_includes = tuple(
        IncludeTarget("Encounter", "participant", t, _include_child(_P, t))
        for t in PARTICIPANT_TYPES
        if t in _MODELED
    )

    return SearchRegistry(
        resource_type="Encounter",
        params={p.name: p for p in params},
        # Σ elements in the R4 Encounter definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "status",
                "class",
                "type",
                "serviceType",
                "subject",
                "episodeOfCare",
                "participant",
                "appointment",
                "reasonCode",
                "reasonReference",
                "diagnosis",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "class"}),
        # One include per target type that is a resource here (Group, Account, ... are not rebuilt
        # resources).
        includes=(
            IncludeTarget(
                "Encounter",
                "based-on",
                "ServiceRequest",
                _include_child(_R, "ServiceRequest", _R.param == "based-on"),
            ),
            IncludeTarget(
                "Encounter",
                "appointment",
                "Appointment",
                _include_child(_R, "Appointment", _R.param == "appointment"),
            ),
            IncludeTarget(
                "Encounter",
                "episode-of-care",
                "EpisodeOfCare",
                _include_child(_R, "EpisodeOfCare", _R.param == "episode-of-care"),
            ),
            IncludeTarget(
                "Encounter", "location", "Location", _include_child(_L, "Location")
            ),
            *participant_includes,
            IncludeTarget(
                "Encounter",
                "practitioner",
                "Practitioner",
                _include_child(_P, "Practitioner"),
            ),
            IncludeTarget(
                "Encounter", "patient", "Patient", _include_column("subject", "Patient")
            ),
            IncludeTarget(
                "Encounter", "subject", "Patient", _include_column("subject", "Patient")
            ),
            IncludeTarget(
                "Encounter",
                "diagnosis",
                "Condition",
                _include_child(_R, "Condition", _R.param == "diagnosis"),
            ),
            IncludeTarget(
                "Encounter",
                "reason-reference",
                "Condition",
                _include_child(_R, "Condition", _R.param == "reason-reference"),
            ),
            IncludeTarget(
                "Encounter",
                "diagnosis",
                "Procedure",
                _include_child(_R, "Procedure", _R.param == "diagnosis"),
            ),
            IncludeTarget(
                "Encounter",
                "reason-reference",
                "Procedure",
                _include_child(_R, "Procedure", _R.param == "reason-reference"),
            ),
            IncludeTarget(
                "Encounter",
                "reason-reference",
                "Observation",
                _include_child(_R, "Observation", _R.param == "reason-reference"),
            ),
            IncludeTarget(
                "Encounter",
                "part-of",
                "Encounter",
                _include_column("part_of", "Encounter"),
            ),
            IncludeTarget(
                "Encounter",
                "service-provider",
                "Organization",
                _include_column("service_provider", "Organization"),
            ),
        ),
        # An Encounter that is part of another one points back at it.
        revincludes=(
            *column_communication_revincludes(
                ("encounter",), "encounter", "Encounter", lambda x: x.encounter_id
            ),
            *column_flag_revincludes(
                ("encounter",), "encounter", "Encounter", lambda x: x.encounter_id
            ),
            *column_task_revincludes(
                ("encounter",), "encounter", "Encounter", lambda x: x.encounter_id
            ),
            *column_medication_dispense_revincludes(
                ("context",), "context", "Encounter", lambda x: x.encounter_id
            ),
            *column_medication_administration_revincludes(
                ("context",), "context", "Encounter", lambda x: x.encounter_id
            ),
            *column_medication_statement_revincludes(
                ("context",), "context", "Encounter", lambda x: x.encounter_id
            ),
            *column_questionnaire_response_revincludes(
                ("encounter",), "encounter", "Encounter", lambda x: x.encounter_id
            ),
            *reference_document_reference_revincludes(
                "encounter", "Encounter", lambda x: x.encounter_id
            ),
            *column_care_plan_revincludes(
                ("encounter",), "encounter", "Encounter", lambda x: x.encounter_id
            ),
            *column_care_team_revincludes(
                ("encounter",), "encounter", "Encounter", lambda e: e.encounter_id
            ),
            *column_medication_request_revincludes(
                ("encounter",), "encounter", "Encounter", lambda e: e.encounter_id
            ),
            *column_service_request_revincludes(
                ("encounter",), "encounter", "Encounter", lambda e: e.encounter_id
            ),
            IncludeTarget(
                "Encounter",
                "part-of",
                "Encounter",
                revinclude_encounters_via_column(
                    "part_of", "Encounter", lambda e: e.encounter_id
                ),
                reverse=True,
            ),
            # Condition.encounter points here.
            *encounter_condition_revincludes(lambda e: e.encounter_id),
            *encounter_procedure_revincludes(lambda e: e.encounter_id),
            *encounter_report_revincludes(lambda e: e.encounter_id),
            *column_risk_revincludes(
                ("encounter",), "encounter", "Encounter", lambda e: e.encounter_id
            ),
            *column_observation_revincludes(
                ("encounter",), "encounter", "Encounter", lambda e: e.encounter_id
            ),
            *column_impression_revincludes(
                ("encounter",), "encounter", "Encounter", lambda e: e.encounter_id
            ),
        ),
        default_sort=lambda: [E.encounter_id.desc()],
    )
