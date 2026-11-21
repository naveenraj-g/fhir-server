"""
FHIR R4 AllergyIntolerance search parameters
(https://www.hl7.org/fhir/R4/allergyintolerance.html#search) plus the common
`_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL,
`_sort`, `_include` / `_revinclude`, and the OpenAPI docs all come from
allergy_intolerance_search() below. Same arrangement as
app.repository.encounter.search (references held as columns, one shared token
table, date ranges) and app.repository.appointment_response.search
(multi-target references).

Each parameter's SQL reads only the search index (AllergyIntoleranceModel's
columns and child tables, see its docstring) — never `content`.
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
from app.repository._clinical_impression_revinclude import reference_impression_revincludes
from app.models.allergy_intolerance import (
    ACTOR_TYPES,
    CRITICALITY_SYSTEM,
    TYPE_SYSTEM,
    AllergyIntoleranceCriticality,
    AllergyIntoleranceIdentifier,
    AllergyIntoleranceModel,
    AllergyIntoleranceReaction,
    AllergyIntoleranceToken,
    AllergyIntoleranceType,
)

A = AllergyIntoleranceModel
_I = AllergyIntoleranceIdentifier
_Tk = AllergyIntoleranceToken
_Rx = AllergyIntoleranceReaction

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
    "RelatedPerson": ("app.models.related_person", "RelatedPersonModel", "related_person_id",
                      "app.repository.related_person.search", "related_person_search"),
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
    return exists(select(literal(1)).where(model.allergy_intolerance_pk == A.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return select(fn(column)).where(model.allergy_intolerance_pk == A.id, *conditions).scalar_subquery()

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(A.updated_at, A.created_at)


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition. Does
    not correlate to the outer row — it ranges over the referenced resource."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


# ── _id / type / criticality ─────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system or not (token.code or "").isdigit():  # ids are the numeric public id
        return false()
    return A.allergy_intolerance_id == int(token.code)


def _code_column(column, enum_cls, system: str):
    """(match, present) for a `code` element held as an Enum column and bound to
    one code system: `code` or `system|code`; another system or `|code` (no
    system) never matches; an unknown code matches nothing (rather than
    failing the Postgres enum cast)."""

    def match(value, modifier, ctx):
        token = parse_token(value)
        if token.system is not None and token.system != system:
            return false()
        if token.code is None:
            return column.is_not(None)
        try:
            return column == enum_cls(token.code)
        except ValueError:
            return false()

    return match, lambda ctx: column.is_not(None)


# ── dates: date / last-date / onset (a dateTime held as the range it covers) ──


def _recorded_date_match(value, modifier, ctx):
    return period_match(A.recorded_date_start, A.recorded_date_end, value)


def _last_occurrence_match(value, modifier, ctx):
    return period_match(A.last_occurrence_start, A.last_occurrence_end, value)


def _onset_match(value, modifier, ctx):
    # AllergyIntolerance.reaction.onset: any reaction's onset.
    return _exists(_Rx, period_match(_Rx.onset_start, _Rx.onset_end, value))


# ── identifier / the seven token parameters ──────────────────────────────────


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


# ── references held as columns: patient / recorder / asserter ────────────────


def _column_ref(prefix: str, targets: tuple[str, ...]):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*`
    columns on the allergy_intolerance row."""
    ref, type_, id_ = (getattr(A, f"{prefix}_{part}") for part in ("reference", "type", "id"))
    ident_system, ident_value = getattr(A, f"{prefix}_identifier_system"), getattr(A, f"{prefix}_identifier_value")

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return token_condition(ident_system, ident_value, parse_token(value))
        # `modifier` is a target type (asserter:Practitioner=30001) or None; a bare id
        # with several targets is ambiguous and is rejected by reference_target().
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return or_(ref.is_not(None), ident_value.is_not(None))

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# ── _include / _revinclude ───────────────────────────────────────────────────


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


def _include_column(prefix: str, resource_type: str):
    """_include of a reference held as columns (`patient`, `recorder`,
    `asserter`): the rows of `resource_type` these allergies point at."""

    async def fetch(session, ctx, allergies):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {getattr(a, id_) for a in allergies if getattr(a, type_) == resource_type and getattr(a, id_)}
        if not ids:
            return []
        model, id_col = _model(resource_type)
        return await _fetch(session, select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids)))

    return fetch


def revinclude_allergies_via_column(prefix: str, resource_type: str, key):
    """_revinclude=AllergyIntolerance:patient / :recorder / :asserter —
    allergies whose column reference points at one of these rows (matched on
    the public id `key(row)`). Declared on the registry of each target type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        type_, id_ = getattr(A, f"{prefix}_type"), getattr(A, f"{prefix}_id")
        return await _fetch(session, select(A).where(A.tenant_id == ctx.tenant_id, type_ == resource_type, id_.in_(ids)))

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders AllergyIntolerance rows."""
    from app.fhir.mappers.allergy_intolerance import to_fhir_allergy_intolerance
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "AllergyIntolerance",
            lambda a: a.allergy_intolerance_id,
            to_fhir_allergy_intolerance,
            "allergy-intolerances",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_CODE = frozenset({"not", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {"identifier": "`:identifier` — match the logical identifier of a target that has no resource here."}


@cache
def allergy_intolerance_search() -> SearchRegistry:
    _register_kind()

    def token(name, description, expression, example, modifiers=_TOKEN):
        match, present, sort = _token_param(name)
        return SearchParam(name, "token", description, expression, match, present, modifiers, sort=sort, example=example)

    def column_ref(name, description, expression, prefix, targets, example):
        match, present, chain, sort = _column_ref(prefix, targets)
        modeled = [t for t in targets if t in _MODELED]
        return SearchParam(
            name, "reference", description, expression, match, present, _REFERENCE, targets=targets, chain=chain,
            chain_targets={t: _registry_of(t) for t in modeled}, sort=sort, example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    type_match, type_present = _code_column(A.type, AllergyIntoleranceType, TYPE_SYSTEM)
    criticality_match, criticality_present = _code_column(
        A.criticality, AllergyIntoleranceCriticality, CRITICALITY_SYSTEM
    )

    params = [
        SearchParam(
            "_id", "token", "Logical id of the resource (the public allergy intolerance id)", "Resource.id",
            _id_match, lambda ctx: true(), frozenset({"not", "missing"}),
            sort=lambda: A.allergy_intolerance_id, example="260001",
        ),
        SearchParam(
            "_lastUpdated", "date", "When the resource last changed (meta.lastUpdated)", "Resource.meta.lastUpdated",
            lambda v, m, ctx: date_match(last_updated(), v), lambda ctx: true(),
            sort=last_updated, example="ge2024-01-01",
        ),
        column_ref(
            "asserter", "Source of the information about the allergy", "AllergyIntolerance.asserter", "asserter",
            ACTOR_TYPES, "Practitioner/30001",
        ),
        token(
            "category", "food | medication | environment | biologic", "AllergyIntolerance.category",
            "http://hl7.org/fhir/allergy-intolerance-category|food", modifiers=_CODE,
        ),
        token(
            "clinical-status", "active | inactive | resolved", "AllergyIntolerance.clinicalStatus",
            "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical|active",
        ),
        token(
            "code", "Code that identifies the allergy or intolerance",
            "AllergyIntolerance.code | AllergyIntolerance.reaction.substance", "http://snomed.info/sct|91936005",
        ),
        SearchParam(
            "criticality", "token",
            f"low | high | unable-to-assess (system {CRITICALITY_SYSTEM})", "AllergyIntolerance.criticality",
            criticality_match, criticality_present, _CODE, sort=lambda: A.criticality, example="high",
        ),
        SearchParam(
            "date", "date", "Date first version of the resource instance was recorded", "AllergyIntolerance.recordedDate",
            _recorded_date_match, lambda ctx: A.recorded_date_start.is_not(None) | A.recorded_date_end.is_not(None),
            sort=lambda: A.recorded_date_start, example="ge2026-01-01",
        ),
        SearchParam(
            "identifier", "token", "External ids for this item", "AllergyIntolerance.identifier",
            _identifier_match, lambda ctx: _exists(_I), frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I), example="urn:allergies|AI-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "last-date", "date", "Date(/time) of last known occurrence of a reaction",
            "AllergyIntolerance.lastOccurrence", _last_occurrence_match,
            lambda ctx: A.last_occurrence_start.is_not(None) | A.last_occurrence_end.is_not(None),
            sort=lambda: A.last_occurrence_start, example="ge2026-01-01",
        ),
        token(
            "manifestation", "Clinical symptoms/signs associated with the Event",
            "AllergyIntolerance.reaction.manifestation", "http://snomed.info/sct|271807003",
        ),
        SearchParam(
            "onset", "date", "Date(/time) when manifestations showed", "AllergyIntolerance.reaction.onset",
            _onset_match, lambda ctx: _exists(_Rx, or_(_Rx.onset_start.is_not(None), _Rx.onset_end.is_not(None))),
            sort=lambda: _child_sort(_Rx.onset_start, _Rx), example="ge2026-01-01",
        ),
        column_ref(
            "patient", "Who the sensitivity is for", "AllergyIntolerance.patient", "patient", ("Patient",),
            "Patient/10001",
        ),
        column_ref(
            "recorder", "Who recorded the sensitivity", "AllergyIntolerance.recorder", "recorder", ACTOR_TYPES,
            "Practitioner/30001",
        ),
        token(
            "route", "How the subject was exposed to the substance", "AllergyIntolerance.reaction.exposureRoute",
            "http://snomed.info/sct|26643006",
        ),
        token(
            "severity", "mild | moderate | severe (of event as a whole)", "AllergyIntolerance.reaction.severity",
            "http://hl7.org/fhir/reaction-event-severity|severe", modifiers=_CODE,
        ),
        SearchParam(
            "type", "token",
            f"allergy | intolerance - Underlying mechanism (if known) (system {TYPE_SYSTEM})",
            "AllergyIntolerance.type", type_match, type_present, _CODE, sort=lambda: A.type, example="allergy",
        ),
        token(
            "verification-status", "unconfirmed | confirmed | refuted | entered-in-error",
            "AllergyIntolerance.verificationStatus",
            "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification|confirmed",
        ),
    ]

    # One include per target type, so `_include=AllergyIntolerance:asserter` brings in all
    # of them and `AllergyIntolerance:asserter:Patient` just the Patients.
    actor_includes = tuple(
        IncludeTarget("AllergyIntolerance", param, t, _include_column(param, t))
        for param in ("asserter", "recorder")
        for t in ACTOR_TYPES
    )

    return SearchRegistry(
        resource_type="AllergyIntolerance",
        params={p.name: p for p in params},
        # Σ elements in the R4 AllergyIntolerance definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {"clinicalStatus", "verificationStatus", "type", "category", "criticality", "code", "patient", "asserter"}
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"patient"}),
        includes=(
            IncludeTarget("AllergyIntolerance", "patient", "Patient", _include_column("patient", "Patient")),
            *actor_includes,
        ),
        # Nothing that references an AllergyIntolerance is on the engine.
        # ClinicalImpression.problem points here.
        revincludes=(
            *reference_impression_revincludes('problem', 'AllergyIntolerance', lambda a: a.allergy_intolerance_id),
        ),
        default_sort=lambda: [A.allergy_intolerance_id.desc()],
    )
