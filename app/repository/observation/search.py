"""
FHIR R4 Observation search parameters
(https://www.hl7.org/fhir/R4/observation.html#search) plus the common `_id` / `_lastUpdated`,
declared once for app.fhir.search: parsing, SQL, `_sort`, `_include` / `_revinclude`, and the
OpenAPI docs all come from observation_search() below. Same arrangement as
app.repository.detected_issue.search (single references held as columns, the repeating ones in
one shared reference table, one shared token table), plus:

  - `ObservationValue`, one table for the value[x] parameters that are not tokens (a Quantity, a
    string, a dateTime/Period), and a `slot` on both it and the token table saying which element
    (the Observation = 0, its n-th component = n) a row came from;
  - the `combo-*` parameters, which are the union of an Observation-level and a component-level
    parameter (`param IN (...)`);
  - the engine's first **composite** searches (app.fhir.search.composite): `code-value-quantity`
    and friends pair a code with a value *of the same element*, by joining a token row and a
    value row on `slot`.

Each parameter's SQL reads only the search index (ObservationModel's columns and child tables,
see its docstring) — never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true
from sqlalchemy.orm import aliased

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.composite import split_composite
from app.fhir.search.quantity import quantity_match
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
from app.repository._medication_statement_revinclude import reference_medication_statement_revincludes
from app.repository._questionnaire_response_revinclude import (
    reference_questionnaire_response_revincludes,
)
from app.repository._diagnostic_report_revinclude import result_report_revincludes
from app.repository._appointment_revinclude import reason_appointment_revincludes
from app.repository._clinical_impression_revinclude import (
    reference_impression_revincludes,
)
from app.repository._encounter_revinclude import reference_encounter_revincludes
from app.repository._procedure_revinclude import reason_procedure_revincludes
from app.repository._immunization_revinclude import (
    reaction_immunization_revincludes,
    reason_immunization_revincludes,
)
from app.models.observation import (
    DEVICE_TYPES,
    REFERENCE_TYPES,
    SUBJECT_TYPES,
    ObservationIdentifier,
    ObservationModel,
    ObservationReference,
    ObservationStatus,
    ObservationToken,
    ObservationValue,
)

M = ObservationModel
_I = ObservationIdentifier
_Tk = ObservationToken
_V = ObservationValue
_R = ObservationReference

# Observation.status is a `code` from the R4 observation-status system.
_STATUS_SYSTEM = "http://hl7.org/fhir/observation-status"

# Reference targets that are searchable resources on this server: the model to
# join for chaining / `_include`, and its registry.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = {
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
    "Encounter": (
        "app.models.encounter",
        "EncounterModel",
        "encounter_id",
        "app.repository.encounter.search",
        "encounter_search",
    ),
    "Appointment": (
        "app.models.appointment",
        "AppointmentModel",
        "appointment_id",
        "app.repository.appointment.search",
        "appointment_search",
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
    "FamilyMemberHistory": (
        "app.models.family_member_history",
        "FamilyMemberHistoryModel",
        "family_member_history_id",
        "app.repository.family_member_history.search",
        "family_member_history_search",
    ),
    "RiskAssessment": (
        "app.models.risk_assessment",
        "RiskAssessmentModel",
        "risk_assessment_id",
        "app.repository.risk_assessment.search",
        "risk_assessment_search",
    ),
    "ClinicalImpression": (
        "app.models.clinical_impression",
        "ClinicalImpressionModel",
        "clinical_impression_id",
        "app.repository.clinical_impression.search",
        "clinical_impression_search",
    ),
    "DetectedIssue": (
        "app.models.detected_issue",
        "DetectedIssueModel",
        "detected_issue_id",
        "app.repository.detected_issue.search",
        "detected_issue_search",
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
    return exists(select(literal(1)).where(model.observation_pk == M.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.observation_pk == M.id, *conditions)
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
    return M.observation_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the observation-status system: `code` or `system|code`;
    another system or `|code` (no system) never matches; an unknown code matches nothing
    (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == ObservationStatus(token.code)
    except ValueError:
        return false()


def _date_match(value, modifier, ctx):
    # Observation.effective[x] (dateTime, instant, Period or Timing): matched as the range it covers.
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


# ── tokens: one table, `param` + `slot` ──────────────────────────────────────


def _token_param(*params: str):
    """(match, present, sort) for a token parameter held in the shared token table: the rows
    whose `param` is any of `params` (one for a plain parameter, two for a `combo-*` one)."""

    def match(value, modifier, ctx):
        return _exists(
            _Tk,
            _Tk.param.in_(params),
            coded_token_match(
                _Tk.system, _Tk.code, value, modifier, (_Tk.text_norm, _Tk.display_norm)
            ),
        )

    def present(ctx):
        return _exists(_Tk, _Tk.param.in_(params))

    def sort():
        return _child_sort(_Tk.code, _Tk, _Tk.param.in_(params))

    return match, present, sort


# ── values: quantity / string / date ─────────────────────────────────────────


def _quantity_param(*params: str):
    """(match, present, sort) for a quantity parameter held in the value table."""

    def match(value, modifier, ctx):
        return _exists(
            _V,
            _V.param.in_(params),
            quantity_match(
                _V.quantity_value,
                _V.quantity_system,
                _V.quantity_code,
                _V.quantity_unit,
                value,
            ),
        )

    def present(ctx):
        return _exists(_V, _V.param.in_(params))

    def sort():
        return _child_sort(_V.quantity_value, _V, _V.param.in_(params))

    return match, present, sort


def _string_match(value, modifier, ctx):
    # Only the normalized form is stored, so `:exact` is not offered; the default (starts-with)
    # and `:contains` read it.
    return _exists(
        _V,
        _V.param == "value-string",
        string_match(_V.string_norm, _V.string_norm, value, modifier),
    )


def _value_date_match(value, modifier, ctx):
    return _exists(
        _V, _V.param == "value-date", period_match(_V.date_start, _V.date_end, value)
    )


# ── composites: a code and a value of the same element ───────────────────────


def _composite(
    code_params: tuple[str, ...], value_kind: str, value_params: tuple[str, ...]
):
    """A `code$value` composite: some element (slot) has a coding of one of `code_params` matching
    the first part *and* a value of `value_kind` (`concept`, `quantity`, `string` or `date`) on one
    of `value_params` matching the second part. Both rows must carry the same `slot`, which is what
    stops a code of one component pairing with the value of another. (`,` ORs several composites
    — the parser splits it; `$` splits the parts here.)"""

    def match(value, modifier, ctx):
        code_part, value_part = split_composite(value, 2)
        code = aliased(_Tk)
        if value_kind == "concept":
            other = aliased(_Tk)
            paired = exists(
                select(literal(1))
                .where(
                    other.observation_pk == M.id,
                    other.slot == code.slot,
                    other.param.in_(value_params),
                    token_match(other.system, other.code, value_part),
                )
                .correlate(M, code)
            )
        else:
            other = aliased(_V)
            if value_kind == "quantity":
                value_condition = quantity_match(
                    other.quantity_value,
                    other.quantity_system,
                    other.quantity_code,
                    other.quantity_unit,
                    value_part,
                )
            elif value_kind == "string":
                value_condition = string_match(
                    other.string_norm, other.string_norm, value_part, None
                )
            else:  # date
                value_condition = period_match(
                    other.date_start, other.date_end, value_part
                )
            paired = exists(
                select(literal(1))
                .where(
                    other.observation_pk == M.id,
                    other.slot == code.slot,
                    other.param.in_(value_params),
                    value_condition,
                )
                .correlate(M, code)
            )
        return exists(
            select(literal(1))
            .where(
                code.observation_pk == M.id,
                code.param.in_(code_params),
                token_match(code.system, code.code, code_part),
                paired,
            )
            .correlate(M)
        )

    return match


# ── references held as columns: subject / patient / encounter / specimen / device ──


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    observation row. `narrowed` restricts a multi-target element to one type (`patient` is
    `subject` resolved to a Patient)."""
    ref, type_, id_ = (
        getattr(M, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(M, f"{prefix}_identifier_system"),
        getattr(M, f"{prefix}_identifier_value"),
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


# ── based-on / part-of / focus / has-member / derived-from / performer: the shared reference table ──


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


def _include_column(prefix: str, resource_type: str):
    """_include of a reference held as columns: the rows of `resource_type` these observations
    point at."""

    async def fetch(session, ctx, observations):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(r, id_)
            for r in observations
            if getattr(r, type_) == resource_type and getattr(r, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_reference(param: str, resource_type: str):
    """_include of a reference-table parameter: the rows of `resource_type`."""

    async def fetch(session, ctx, observations):
        ids = select(_R.reference_id).where(
            _R.observation_pk.in_({r.id for r in observations}),
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


def revinclude_observations_via_column(prefix: str, resource_type: str, key):
    """_revinclude=Observation:subject / :patient / :encounter — observations whose column
    reference points at one of these rows (matched on the public id `key(row)`). Declared on the
    registry of each target type."""

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


def revinclude_observations_via_reference(param: str, resource_type: str, key):
    """_revinclude=Observation:performer / :part-of / :has-member / ... — observations with a row
    in the reference table pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.observation_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Observation rows."""
    from app.fhir.mappers.observation import to_fhir_observation
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "Observation",
            lambda r: r.observation_id,
            to_fhir_observation,
            "observations",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}
_COMPOSITE_DOC = (
    " A composite search: `<part>$<part>` (e.g. `code$value`), both parts on the same element — the "
    "Observation itself or, for the `component-*` and `combo-*` forms, one component."
)


@cache
def observation_search() -> SearchRegistry:
    _register_kind()

    def token(name, description, expression, example, *params):
        match, present, sort = _token_param(*(params or (name,)))
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

    def quantity(name, description, expression, example, *params):
        match, present, sort = _quantity_param(*(params or (name,)))
        return SearchParam(
            name,
            "quantity",
            description,
            expression,
            match,
            present,
            frozenset({"missing"}),
            sort=sort,
            example=example,
        )

    def composite(
        name, description, expression, example, code_params, value_kind, value_params
    ):
        return SearchParam(
            name,
            "composite",
            description + _COMPOSITE_DOC,
            expression,
            _composite(code_params, value_kind, value_params),
            lambda ctx: true(),
            frozenset(),
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

    def table_ref(name, description, expression, example):
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

    loinc_bp = "http://loinc.org|85354-9"
    code_value_quantity = (
        "http://loinc.org|8480-6$gt100|http://unitsofmeasure.org|mm[Hg]"
    )
    value_string_match, value_string_present = (
        _string_match,
        lambda ctx: _exists(_V, _V.param == "value-string"),
    )
    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public observation id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.observation_id,
            example="160001",
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
        table_ref(
            "based-on",
            "Reference to the service request.",
            "Observation.basedOn",
            "ServiceRequest/80001",
        ),
        token(
            "category",
            "The classification of the type of observation",
            "Observation.category",
            "http://terminology.hl7.org/CodeSystem/observation-category|vital-signs",
        ),
        token("code", "The code of the observation type", "Observation.code", loinc_bp),
        composite(
            "code-value-concept",
            "Both code and coded value, on the same Observation",
            "Observation: code | value.as(CodeableConcept)",
            "http://loinc.org|1234-5$http://snomed.info/sct|260385009",
            ("code",),
            "concept",
            ("value-concept",),
        ),
        composite(
            "code-value-date",
            "Both code and date/time value, on the same Observation",
            "Observation: code | value.as(DateTime) | value.as(Period)",
            "http://loinc.org|1234-5$ge2024-01-01",
            ("code",),
            "date",
            ("value-date",),
        ),
        composite(
            "code-value-quantity",
            "Both code and quantity value, on the same Observation",
            "Observation: code | value.as(Quantity)",
            code_value_quantity,
            ("code",),
            "quantity",
            ("value-quantity",),
        ),
        composite(
            "code-value-string",
            "Both code and string value, on the same Observation",
            "Observation: code | value.as(string)",
            "http://loinc.org|1234-5$positive",
            ("code",),
            "string",
            ("value-string",),
        ),
        token(
            "combo-code",
            "The code of the observation type or component type",
            "Observation.code | Observation.component.code",
            loinc_bp,
            "code",
            "component-code",
        ),
        composite(
            "combo-code-value-concept",
            "Code and coded value, on the Observation or one of its components",
            "Observation | Observation.component: combo-code | combo-value-concept",
            "http://loinc.org|1234-5$http://snomed.info/sct|260385009",
            ("code", "component-code"),
            "concept",
            ("value-concept", "component-value-concept"),
        ),
        composite(
            "combo-code-value-quantity",
            "Code and quantity value, on the Observation or one of its components",
            "Observation | Observation.component: combo-code | combo-value-quantity",
            code_value_quantity,
            ("code", "component-code"),
            "quantity",
            ("value-quantity", "component-value-quantity"),
        ),
        token(
            "combo-data-absent-reason",
            "The reason why the expected value in the element Observation.value[x] or "
            "Observation.component.value[x] is missing.",
            "Observation.dataAbsentReason | Observation.component.dataAbsentReason",
            "unknown",
            "data-absent-reason",
            "component-data-absent-reason",
        ),
        token(
            "combo-value-concept",
            "The value or component value of the observation, if the value is a "
            "CodeableConcept",
            "(Observation.value as CodeableConcept) | (Observation.component.value as CodeableConcept)",
            "http://snomed.info/sct|260385009",
            "value-concept",
            "component-value-concept",
        ),
        quantity(
            "combo-value-quantity",
            "The value or component value of the observation, if the value is a Quantity",
            "(Observation.value as Quantity) | (Observation.component.value as Quantity)",
            "gt100|http://unitsofmeasure.org|mm[Hg]",
            "value-quantity",
            "component-value-quantity",
        ),
        token(
            "component-code",
            "The component code of the observation type",
            "Observation.component.code",
            "http://loinc.org|8480-6",
        ),
        composite(
            "component-code-value-concept",
            "Both component code and coded value, on the same component",
            "Observation.component: component-code | component-value-concept",
            "http://loinc.org|1234-5$http://snomed.info/sct|260385009",
            ("component-code",),
            "concept",
            ("component-value-concept",),
        ),
        composite(
            "component-code-value-quantity",
            "Both component code and quantity value, on the same component",
            "Observation.component: component-code | component-value-quantity",
            code_value_quantity,
            ("component-code",),
            "quantity",
            ("component-value-quantity",),
        ),
        token(
            "component-data-absent-reason",
            "The reason why the expected value in the element "
            "Observation.component.value[x] is missing.",
            "Observation.component.dataAbsentReason",
            "unknown",
        ),
        token(
            "component-value-concept",
            "The value of the component observation, if the value is a CodeableConcept",
            "(Observation.component.value as CodeableConcept)",
            "http://snomed.info/sct|260385009",
        ),
        quantity(
            "component-value-quantity",
            "The value of the component observation, if the value is a Quantity",
            "(Observation.component.value as Quantity)",
            "gt100|http://unitsofmeasure.org|mm[Hg]",
        ),
        token(
            "data-absent-reason",
            "The reason why the expected value in the element Observation.value[x] is missing.",
            "Observation.dataAbsentReason",
            "unknown",
        ),
        SearchParam(
            "date",
            "date",
            "Obtained date/time. If the obtained element is a period, a date that falls in the period",
            "Observation.effective",
            _date_match,
            lambda ctx: M.date_start.is_not(None) | M.date_end.is_not(None),
            sort=lambda: M.date_start,
            example="ge2026-01-01",
        ),
        table_ref(
            "derived-from",
            "Related measurements the observation is made from",
            "Observation.derivedFrom",
            "Observation/160001",
        ),
        column_ref(
            "device",
            "The Device that generated the observation data.",
            "Observation.device",
            "device",
            DEVICE_TYPES,
            "Device/1",
        ),
        column_ref(
            "encounter",
            "Encounter related to the observation",
            "Observation.encounter",
            "encounter",
            ("Encounter",),
            "Encounter/20001",
        ),
        table_ref(
            "focus",
            "The focus of an observation when the focus is not the patient of record (Reference(Any): "
            "needs a type)",
            "Observation.focus",
            "Condition/120001",
        ),
        table_ref(
            "has-member",
            "Related resource that belongs to the Observation group",
            "Observation.hasMember",
            "Observation/160001",
        ),
        SearchParam(
            "identifier",
            "token",
            "The unique id for a particular observation",
            "Observation.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:observations|OBS-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        token(
            "method",
            "The method used for the observation",
            "Observation.method",
            "http://snomed.info/sct|39857003",
        ),
        table_ref(
            "part-of",
            "Part of referenced event",
            "Observation.partOf",
            "Procedure/100001",
        ),
        column_ref(
            "patient",
            "The subject that the observation is about (if patient)",
            "Observation.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        table_ref(
            "performer",
            "Who performed the observation",
            "Observation.performer",
            "Practitioner/30001",
        ),
        column_ref(
            "specimen",
            "Specimen used for this observation",
            "Observation.specimen",
            "specimen",
            ("Specimen",),
            "Specimen/310001",
        ),
        SearchParam(
            "status",
            "token",
            f"registered | preliminary | final | amended + (system {_STATUS_SYSTEM})",
            "Observation.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="final",
        ),
        column_ref(
            "subject",
            "The subject that the observation is about",
            "Observation.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
        token(
            "value-concept",
            "The value of the observation, if the value is a CodeableConcept",
            "(Observation.value as CodeableConcept)",
            "http://snomed.info/sct|260385009",
        ),
        SearchParam(
            "value-date",
            "date",
            "The value of the observation, if the value is a date or period of time",
            "(Observation.value as dateTime) | (Observation.value as Period)",
            _value_date_match,
            lambda ctx: _exists(_V, _V.param == "value-date"),
            sort=lambda: _child_sort(_V.date_start, _V, _V.param == "value-date"),
            example="ge2026-01-01",
        ),
        quantity(
            "value-quantity",
            "The value of the observation, if the value is a Quantity",
            "(Observation.value as Quantity)",
            "gt100|http://unitsofmeasure.org|mm[Hg]",
        ),
        SearchParam(
            "value-string",
            "string",
            "The value of the observation, if the value is a string, and also searches in "
            "CodeableConcept.text",
            "(Observation.value as string) | (Observation.value as CodeableConcept).text",
            value_string_match,
            value_string_present,
            frozenset({"contains", "missing"}),
            sort=lambda: _child_sort(_V.string_norm, _V, _V.param == "value-string"),
            example="positive",
        ),
    ]

    def column_includes(param, prefix, targets):
        # One include per target type that is a resource here, so `_include=Observation:performer`
        # brings in all of them and `Observation:performer:Practitioner` just the Practitioners.
        return tuple(
            IncludeTarget("Observation", param, t, _include_column(prefix, t))
            for t in targets
            if t in _MODELED
        )

    def table_includes(param):
        return tuple(
            IncludeTarget("Observation", param, t, _include_reference(param, t))
            for t in REFERENCE_TYPES[param]
            if t in _MODELED
        )

    key = lambda r: r.observation_id  # noqa: E731
    return SearchRegistry(
        resource_type="Observation",
        params={p.name: p for p in params},
        # Σ elements in the R4 Observation definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "status",
                "code",
                "subject",
                "focus",
                "encounter",
                "effectiveDateTime",
                "effectivePeriod",
                "effectiveTiming",
                "effectiveInstant",
                "issued",
                "performer",
                "valueQuantity",
                "valueCodeableConcept",
                "valueString",
                "valueBoolean",
                "valueInteger",
                "valueRange",
                "valueRatio",
                "valueSampledData",
                "valueTime",
                "valueDateTime",
                "valuePeriod",
                "hasMember",
                "derivedFrom",
                "component",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "code"}),
        includes=(
            IncludeTarget(
                "Observation",
                "patient",
                "Patient",
                _include_column("subject", "Patient"),
            ),
            *column_includes("subject", "subject", SUBJECT_TYPES),
            IncludeTarget(
                "Observation",
                "specimen",
                "Specimen",
                _include_column("specimen", "Specimen"),
            ),
            IncludeTarget(
                "Observation",
                "encounter",
                "Encounter",
                _include_column("encounter", "Encounter"),
            ),
            *table_includes("based-on"),
            *table_includes("part-of"),
            *table_includes("focus"),
            *table_includes("has-member"),
            *table_includes("derived-from"),
            *table_includes("performer"),
        ),
        # Observation:has-member / :derived-from — the observations that group / derive from these.
        revincludes=(
            *reference_medication_statement_revincludes(
                'part-of', 'Observation', lambda x: x.observation_id
            ),
            *reference_questionnaire_response_revincludes(
                "part-of", "Observation", lambda x: x.observation_id
            ),
            *result_report_revincludes(key),
            *reference_impression_revincludes("investigation", "Observation", key),
            *reference_impression_revincludes("finding-ref", "Observation", key),
            *reason_procedure_revincludes("Observation", key),
            *reason_appointment_revincludes("Observation", key),
            *reference_encounter_revincludes(
                "Observation", key, params=("reason-reference",)
            ),
            *reaction_immunization_revincludes(key),
            *reason_immunization_revincludes("Observation", key),
            IncludeTarget(
                "Observation",
                "has-member",
                "Observation",
                revinclude_observations_via_reference("has-member", "Observation", key),
                reverse=True,
            ),
            IncludeTarget(
                "Observation",
                "derived-from",
                "Observation",
                revinclude_observations_via_reference(
                    "derived-from", "Observation", key
                ),
                reverse=True,
            ),
        ),
        default_sort=lambda: [M.observation_id.desc()],
    )
