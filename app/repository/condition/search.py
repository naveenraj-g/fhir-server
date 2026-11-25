"""
FHIR R4 Condition search parameters
(https://www.hl7.org/fhir/R4/condition.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
condition_search() below. Same arrangement as app.repository.encounter.search
(references held as columns, one shared token table) and
app.repository.allergy_intolerance.search (multi-target `asserter`);
`onset-age` / `abatement-age` are quantity searches over an Age *or* a Range
(app.fhir.search.quantity.quantity_range_match).

Each parameter's SQL reads only the search index (ConditionModel's columns and
child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.quantity import quantity_range_match
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
from app.models.condition import (
    ACTOR_TYPES,
    SUBJECT_TYPES,
    ConditionEvidenceDetail,
    ConditionIdentifier,
    ConditionModel,
    ConditionToken,
)
from app.models.shared.resource_types import ANY_RESOURCE_TYPES
from app.repository._appointment_revinclude import reason_appointment_revincludes
from app.repository._care_plan_revinclude import reference_care_plan_revincludes
from app.repository._clinical_impression_revinclude import (
    reference_impression_revincludes,
)
from app.repository._encounter_revinclude import reference_encounter_revincludes
from app.repository._episode_of_care_revinclude import (
    reference_episode_of_care_revincludes,
)
from app.repository._immunization_revinclude import reason_immunization_revincludes
from app.repository._procedure_revinclude import reason_procedure_revincludes
from app.repository._risk_assessment_revinclude import column_risk_revincludes
from app.repository._search_targets import MODELED

C = ConditionModel
_I = ConditionIdentifier
_Tk = ConditionToken
_Ev = ConditionEvidenceDetail

# `evidence.detail` is Reference(Any): R4 allows every resource type, so the whole R4 list is the target
# list (a plain reference search accepts any valid type; chaining and `_include` follow the
# types that are rebuilt on this server - see app/repository/_search_targets.py).
EVIDENCE_DETAIL_TYPES = ANY_RESOURCE_TYPES

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
    return exists(select(literal(1)).where(model.condition_pk == C.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.condition_pk == C.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(C.updated_at, C.created_at)


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
    return C.condition_id == int(token.code)


# ── dates and strings: recorded-date / onset-date / abatement-date / *-string ──


def _date_range(start, end):
    """(match, present, sort) for a dateTime / Period held as a half-open range."""

    def match(value, modifier, ctx):
        return period_match(start, end, value)

    return match, lambda ctx: or_(start.is_not(None), end.is_not(None)), lambda: start


def _string_param(raw, norm):
    """(match, present, sort) for a 0..1 string held as `x` + `x_norm`."""

    def match(value, modifier, ctx):
        return string_match(raw, norm, value, modifier)

    return match, lambda ctx: raw.is_not(None), lambda: norm


def _age_param(element: str):
    """(match, present, sort) for `onset-age` / `abatement-age`: an Age (a point)
    or a Range held as low / high bounds with one shared unit."""
    low, high = getattr(C, f"{element}_age_low"), getattr(C, f"{element}_age_high")
    system, code, unit = (
        getattr(C, f"{element}_age_{part}") for part in ("system", "code", "unit")
    )

    def match(value, modifier, ctx):
        return quantity_range_match(low, high, system, code, unit, value)

    return (
        match,
        lambda ctx: or_(low.is_not(None), high.is_not(None)),
        lambda: func.coalesce(low, high),
    )


# ── identifier / the eight token parameters ──────────────────────────────────


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


# ── references held as columns: subject / patient / encounter / asserter ─────


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*`
    columns on the condition row. `narrowed` restricts a multi-target element to
    one type (`patient` is `subject` resolved to a Patient)."""
    ref, type_, id_ = (
        getattr(C, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(C, f"{prefix}_identifier_system"),
        getattr(C, f"{prefix}_identifier_value"),
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


# ── evidence-detail ──────────────────────────────────────────────────────────


def _evidence_detail_match(value, modifier, ctx):
    if modifier == "identifier":
        return _exists(
            _Ev,
            token_condition(
                _Ev.reference_identifier_system,
                _Ev.reference_identifier_value,
                parse_token(value),
            ),
        )
    return _exists(
        _Ev,
        reference_match(
            _Ev.reference_type,
            _Ev.reference_id,
            _Ev.reference_reference,
            value,
            modifier,
            ctx,
            EVIDENCE_DETAIL_TYPES,
            str,
        ),
    )


def _evidence_detail_present(ctx):
    return _exists(
        _Ev,
        or_(
            _Ev.reference_reference.is_not(None),
            _Ev.reference_identifier_value.is_not(None),
        ),
    )


def _evidence_detail_chain(target, inner, ctx):
    return _exists(
        _Ev,
        _Ev.reference_type == target,
        _Ev.reference_id.in_(_referenced(target, inner, ctx)),
    )


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
    """_include of a reference held as columns (`subject`, `patient`,
    `encounter`, `asserter`): the rows of `resource_type` these conditions
    point at."""

    async def fetch(session, ctx, conditions):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(c, id_)
            for c in conditions
            if getattr(c, type_) == resource_type and getattr(c, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_evidence_detail(resource_type: str):
    """_include=Condition:evidence-detail[:Type] — the rows of a modeled type the
    evidence points at."""

    async def fetch(session, ctx, conditions):
        ids = select(_Ev.reference_id).where(
            _Ev.condition_pk.in_({c.id for c in conditions}),
            _Ev.reference_type == resource_type,
            _Ev.reference_id.is_not(None),
        )
        return await _load(
            session,
            ctx,
            resource_type,
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


def revinclude_conditions_via_column(prefix: str, resource_type: str, key):
    """_revinclude=Condition:subject / :patient / :encounter / :asserter —
    conditions whose column reference points at one of these rows (matched on
    the public id `key(row)`). Declared on the registry of each target type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        type_, id_ = getattr(C, f"{prefix}_type"), getattr(C, f"{prefix}_id")
        return await _fetch(
            session,
            select(C).where(
                C.tenant_id == ctx.tenant_id, type_ == resource_type, id_.in_(ids)
            ),
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Condition rows."""
    from app.fhir.mappers.condition import to_fhir_condition
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "Condition", lambda c: c.condition_id, to_fhir_condition, "conditions"
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_STRING = frozenset({"exact", "contains", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def condition_search() -> SearchRegistry:
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

    def date(name, description, expression, start, end, example):
        match, present, sort = _date_range(start, end)
        return SearchParam(
            name,
            "date",
            description,
            expression,
            match,
            present,
            sort=sort,
            example=example,
        )

    def string(name, description, expression, raw, norm, example):
        match, present, sort = _string_param(raw, norm)
        return SearchParam(
            name,
            "string",
            description,
            expression,
            match,
            present,
            _STRING,
            sort=sort,
            example=example,
        )

    def age(name, description, expression, element):
        match, present, sort = _age_param(element)
        return SearchParam(
            name,
            "quantity",
            description
            + " (`[prefix]number[|system|code]`; units are compared as written, with "
            "no UCUM conversion; an Age is a point and a Range is compared as a range)",
            expression,
            match,
            present,
            sort=sort,
            example="gt18|http://unitsofmeasure.org|a",
        )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public condition id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: C.condition_id,
            example="120001",
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
        age(
            "abatement-age",
            "Abatement as age or age range",
            "Condition.abatement.as(Age) | Condition.abatement.as(Range)",
            "abatement",
        ),
        date(
            "abatement-date",
            "Date-related abatements (dateTime and period)",
            "Condition.abatement.as(dateTime) | Condition.abatement.as(Period)",
            C.abatement_date_start,
            C.abatement_date_end,
            "ge2026-01-01",
        ),
        string(
            "abatement-string",
            "Abatement as a string",
            "Condition.abatement.as(string)",
            C.abatement_string,
            C.abatement_string_norm,
            "resolved",
        ),
        column_ref(
            "asserter",
            "Person who asserts this condition",
            "Condition.asserter",
            "asserter",
            ACTOR_TYPES,
            "Practitioner/30001",
        ),
        token(
            "body-site",
            "Anatomical location, if relevant",
            "Condition.bodySite",
            "http://snomed.info/sct|368208006",
        ),
        token(
            "category",
            "The category of the condition (problem-list-item | encounter-diagnosis)",
            "Condition.category",
            "http://terminology.hl7.org/CodeSystem/condition-category|problem-list-item",
        ),
        token(
            "clinical-status",
            "The clinical status of the condition (active | recurrence | relapse | inactive | remission | resolved)",
            "Condition.clinicalStatus",
            "http://terminology.hl7.org/CodeSystem/condition-clinical|active",
        ),
        token(
            "code",
            "Code for the condition",
            "Condition.code",
            "http://snomed.info/sct|38341003",
        ),
        column_ref(
            "encounter",
            "Encounter created as part of",
            "Condition.encounter",
            "encounter",
            ("Encounter",),
            "Encounter/20001",
        ),
        token(
            "evidence",
            "Manifestation/symptom",
            "Condition.evidence.code",
            "http://snomed.info/sct|29857009",
        ),
        SearchParam(
            "evidence-detail",
            "reference",
            "Supporting information found elsewhere (Reference(Any): needs a type)",
            "Condition.evidence.detail",
            _evidence_detail_match,
            _evidence_detail_present,
            _REFERENCE,
            targets=EVIDENCE_DETAIL_TYPES,
            chain=_evidence_detail_chain,
            chain_targets={t: _registry_of(t) for t in _MODELED},
            sort=lambda: _child_sort(_Ev.reference_id, _Ev),
            example="Observation/160001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        SearchParam(
            "identifier",
            "token",
            "A unique identifier of the condition record",
            "Condition.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:conditions|C-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        age(
            "onset-age",
            "Onsets as age or age range",
            "Condition.onset.as(Age) | Condition.onset.as(Range)",
            "onset",
        ),
        date(
            "onset-date",
            "Date related onsets (dateTime and Period)",
            "Condition.onset.as(dateTime) | Condition.onset.as(Period)",
            C.onset_date_start,
            C.onset_date_end,
            "ge2026-01-01",
        ),
        string(
            "onset-info",
            "Onsets as a string",
            "Condition.onset.as(string)",
            C.onset_string,
            C.onset_string_norm,
            "childhood",
        ),
        column_ref(
            "patient",
            "Who has the condition?",
            "Condition.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        date(
            "recorded-date",
            "Date record was first recorded",
            "Condition.recordedDate",
            C.recorded_date_start,
            C.recorded_date_end,
            "ge2026-01-01",
        ),
        token(
            "severity",
            "The severity of the condition",
            "Condition.severity",
            "http://snomed.info/sct|24484000",
        ),
        token(
            "stage",
            "Simple summary (disease specific)",
            "Condition.stage.summary",
            "http://snomed.info/sct|14803004",
        ),
        column_ref(
            "subject",
            "Who has the condition?",
            "Condition.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
        token(
            "verification-status",
            "unconfirmed | provisional | differential | confirmed | refuted | entered-in-error",
            "Condition.verificationStatus",
            "http://terminology.hl7.org/CodeSystem/condition-ver-status|confirmed",
        ),
    ]

    # One include per target type that is a resource here, so `_include=Condition:asserter`
    # brings in all of them and `Condition:asserter:Patient` just the Patients.
    asserter_includes = tuple(
        IncludeTarget("Condition", "asserter", t, _include_column("asserter", t))
        for t in ACTOR_TYPES
    )
    evidence_includes = tuple(
        IncludeTarget("Condition", "evidence-detail", t, _include_evidence_detail(t))
        for t in _MODELED
    )

    return SearchRegistry(
        resource_type="Condition",
        params={p.name: p for p in params},
        # Σ elements in the R4 Condition definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "clinicalStatus",
                "verificationStatus",
                "code",
                "bodySite",
                "subject",
                "encounter",
                "onset",
                "onsetDateTime",
                "onsetAge",
                "onsetPeriod",
                "onsetRange",
                "onsetString",
                "recordedDate",
                "recorder",
                "asserter",
                "evidence",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"subject"}),
        includes=(
            IncludeTarget(
                "Condition", "patient", "Patient", _include_column("subject", "Patient")
            ),
            IncludeTarget(
                "Condition", "subject", "Patient", _include_column("subject", "Patient")
            ),
            IncludeTarget(
                "Condition",
                "encounter",
                "Encounter",
                _include_column("encounter", "Encounter"),
            ),
            *asserter_includes,
            *evidence_includes,
        ),
        # Encounter.diagnosis / .reasonReference and Appointment.reasonReference point here.
        revincludes=(
            *reference_episode_of_care_revincludes(
                "condition", "Condition", lambda x: x.condition_id
            ),
            *reference_care_plan_revincludes(
                "condition", "Condition", lambda x: x.condition_id
            ),
            *reference_encounter_revincludes("Condition", lambda c: c.condition_id),
            *reason_appointment_revincludes("Condition", lambda c: c.condition_id),
            *reason_procedure_revincludes("Condition", lambda c: c.condition_id),
            *reason_immunization_revincludes("Condition", lambda c: c.condition_id),
            *column_risk_revincludes(
                ("condition",), "condition", "Condition", lambda c: c.condition_id
            ),
            *reference_impression_revincludes(
                "problem", "Condition", lambda c: c.condition_id
            ),
        ),
        default_sort=lambda: [C.condition_id.desc()],
    )
