"""
FHIR R4 ImmunizationRecommendation search parameters
(https://www.hl7.org/fhir/R4/immunizationrecommendation.html#search) plus the common
`_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
immunization_recommendation_search() below. Same arrangement as
app.repository.immunization.search and app.repository.diagnostic_report.search
(`patient` held as columns, shared token and reference tables).

Each parameter's SQL reads only the search index (ImmunizationRecommendationModel's
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
from app.models.immunization_recommendation import (
    REFERENCE_TYPES,
    ImmunizationRecommendationIdentifier,
    ImmunizationRecommendationModel,
    ImmunizationRecommendationReference,
    ImmunizationRecommendationToken,
)

M = ImmunizationRecommendationModel
_I = ImmunizationRecommendationIdentifier
_Tk = ImmunizationRecommendationToken
_R = ImmunizationRecommendationReference

# Reference targets that are searchable resources on this server: the model to
# join for chaining / `_include`, and its registry.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = {
    "Group": (
        "app.models.group",
        "GroupModel",
        "group_id",
        "app.repository.group.search",
        "group_search",
    ),
    "CareTeam": (
        "app.models.care_team",
        "CareTeamModel",
        "care_team_id",
        "app.repository.care_team.search",
        "care_team_search",
    ),
    "CarePlan": (
        "app.models.care_plan",
        "CarePlanModel",
        "care_plan_id",
        "app.repository.care_plan.search",
        "care_plan_search",
    ),
    "MedicationRequest": (
        "app.models.medication_request",
        "MedicationRequestModel",
        "medication_request_id",
        "app.repository.medication_request.search",
        "medication_request_search",
    ),
    "Medication": (
        "app.models.medication",
        "MedicationModel",
        "medication_id",
        "app.repository.medication.search",
        "medication_search",
    ),
    "ServiceRequest": (
        "app.models.service_request",
        "ServiceRequestModel",
        "service_request_id",
        "app.repository.service_request.search",
        "service_request_search",
    ),
    "Specimen": (
        "app.models.specimen",
        "SpecimenModel",
        "specimen_id",
        "app.repository.specimen.search",
        "specimen_search",
    ),
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
    "Encounter": (
        "app.models.encounter",
        "EncounterModel",
        "encounter_id",
        "app.repository.encounter.search",
        "encounter_search",
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
    "DiagnosticReport": (
        "app.models.diagnostic_report",
        "DiagnosticReportModel",
        "diagnostic_report_id",
        "app.repository.diagnostic_report.search",
        "diagnostic_report_search",
    ),
    "AllergyIntolerance": (
        "app.models.allergy_intolerance",
        "AllergyIntoleranceModel",
        "allergy_intolerance_id",
        "app.repository.allergy_intolerance.search",
        "allergy_intolerance_search",
    ),
    "Immunization": (
        "app.models.immunization",
        "ImmunizationModel",
        "immunization_id",
        "app.repository.immunization.search",
        "immunization_search",
    ),
    "ImmunizationEvaluation": (
        "app.models.immunization_evaluation",
        "ImmunizationEvaluationModel",
        "immunization_evaluation_id",
        "app.repository.immunization_evaluation.search",
        "immunization_evaluation_search",
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
        select(literal(1)).where(
            model.immunization_recommendation_pk == M.id, *conditions
        )
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.immunization_recommendation_pk == M.id, *conditions)
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
    return M.immunization_recommendation_id == int(token.code)


def _date_match(value, modifier, ctx):
    # ImmunizationRecommendation.date is a dateTime: matched as the range it covers.
    return period_match(M.date_start, M.date_end, value)


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


# ── patient: a reference held as columns ─────────────────────────────────────


def _patient_ref():
    """(match, present, chain, sort) for `patient`, held as `patient_*` columns."""
    ref, type_, id_ = M.patient_reference, M.patient_type, M.patient_id

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return token_condition(
                M.patient_identifier_system,
                M.patient_identifier_value,
                parse_token(value),
            )
        return reference_match(type_, id_, ref, value, modifier, ctx, ("Patient",), str)

    def present(ctx):
        return or_(ref.is_not(None), M.patient_identifier_value.is_not(None))

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# ── support / information: references held in the reference table ────────────


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


def _include_patient():
    """_include=ImmunizationRecommendation:patient — the Patients these point at."""

    async def fetch(session, ctx, recommendations):
        ids = {
            r.patient_id
            for r in recommendations
            if r.patient_type == "Patient" and r.patient_id
        }
        return await _load(session, ctx, "Patient", ids)

    return fetch


def _include_reference(param: str, resource_type: str):
    """_include of `support` / `information`: the rows of `resource_type`."""

    async def fetch(session, ctx, recommendations):
        ids = select(_R.reference_id).where(
            _R.immunization_recommendation_pk.in_({r.id for r in recommendations}),
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


def revinclude_recommendations_via_patient(key):
    """_revinclude=ImmunizationRecommendation:patient — recommendations whose patient
    is one of these Patients (matched on the public id `key(row)`)."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        return await _fetch(
            session,
            select(M).where(
                M.tenant_id == ctx.tenant_id,
                M.patient_type == "Patient",
                M.patient_id.in_(ids),
            ),
        )

    return fetch


def revinclude_recommendations_via_reference(param: str, resource_type: str, key):
    """_revinclude=ImmunizationRecommendation:support / :information — recommendations
    with a row in the reference table pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.immunization_recommendation_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders ImmunizationRecommendation rows."""
    from app.fhir.mappers.immunization_recommendation import (
        to_fhir_immunization_recommendation,
    )
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "ImmunizationRecommendation",
            lambda r: r.immunization_recommendation_id,
            to_fhir_immunization_recommendation,
            "immunization-recommendations",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def immunization_recommendation_search() -> SearchRegistry:
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

    def reference(name, description, expression, example):
        # The R4 search-parameter name is also the `param` value in the reference table.
        targets = REFERENCE_TYPES[name]
        match, present, chain, sort = _reference_param(name)
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

    patient_match, patient_present, patient_chain, patient_sort = _patient_ref()

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public immunization recommendation id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.immunization_recommendation_id,
            example="510001",
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
            "Date recommendation(s) created",
            "ImmunizationRecommendation.date",
            _date_match,
            lambda ctx: M.date_start.is_not(None),
            sort=lambda: M.date_start,
            example="ge2026-01-01",
        ),
        SearchParam(
            "identifier",
            "token",
            "Business identifier",
            "ImmunizationRecommendation.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:recommendations|IR-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        reference(
            "information",
            "Patient observations supporting recommendation (Reference(Any): needs a type)",
            "ImmunizationRecommendation.recommendation.supportingPatientInformation",
            "Observation/160001",
        ),
        SearchParam(
            "patient",
            "reference",
            "Who this profile is for",
            "ImmunizationRecommendation.patient",
            patient_match,
            patient_present,
            _REFERENCE,
            targets=("Patient",),
            chain=patient_chain,
            chain_targets={"Patient": _registry_of("Patient")},
            sort=patient_sort,
            example="Patient/10001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        token(
            "status",
            "Vaccine recommendation status",
            "ImmunizationRecommendation.recommendation.forecastStatus",
            "http://terminology.hl7.org/CodeSystem/immunization-recommendation-status|due",
        ),
        reference(
            "support",
            "Past immunizations supporting recommendation",
            "ImmunizationRecommendation.recommendation.supportingImmunization",
            "Immunization/330001",
        ),
        token(
            "target-disease",
            "Disease to be immunized against",
            "ImmunizationRecommendation.recommendation.targetDisease",
            "http://snomed.info/sct|40468003",
        ),
        token(
            "vaccine-type",
            "Vaccine or vaccine group recommendation applies to",
            "ImmunizationRecommendation.recommendation.vaccineCode",
            "http://hl7.org/fhir/sid/cvx|140",
        ),
    ]

    # One include per target type that is a resource here, so `_include=ImmunizationRecommendation:information`
    # brings in every modeled type and `...:information:Condition` just the Conditions.
    information_includes = tuple(
        IncludeTarget(
            "ImmunizationRecommendation",
            "information",
            t,
            _include_reference("information", t),
        )
        for t in REFERENCE_TYPES["information"]
        if t in _MODELED
    )
    support_includes = tuple(
        IncludeTarget(
            "ImmunizationRecommendation", "support", t, _include_reference("support", t)
        )
        for t in REFERENCE_TYPES["support"]
        if t in _MODELED
    )

    return SearchRegistry(
        resource_type="ImmunizationRecommendation",
        params={p.name: p for p in params},
        # Σ elements in the R4 ImmunizationRecommendation definition (beyond id/meta/implicitRules).
        summary_elements=frozenset({"identifier", "patient", "date", "recommendation"}),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"patient", "date", "recommendation"}),
        includes=(
            IncludeTarget(
                "ImmunizationRecommendation", "patient", "Patient", _include_patient()
            ),
            *support_includes,
            *information_includes,
        ),
        revincludes=(),
        default_sort=lambda: [M.immunization_recommendation_id.desc()],
    )
