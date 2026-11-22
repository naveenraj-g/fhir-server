"""
FHIR R4 DetectedIssue search parameters
(https://www.hl7.org/fhir/R4/detectedissue.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`, `_include` /
`_revinclude`, and the OpenAPI docs all come from detected_issue_search() below. Same
arrangement as app.repository.clinical_impression.search (single references held as columns,
one shared token table, the repeating Reference(Any) in one shared reference table).

R4 defines no `status` or `severity` search parameter for DetectedIssue, so neither is indexed.

Each parameter's SQL reads only the search index (DetectedIssueModel's columns and child
tables, see its docstring) — never `content`.
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
from app.models.detected_issue import (
    AUTHOR_TYPES,
    REFERENCE_TYPES,
    DetectedIssueIdentifier,
    DetectedIssueModel,
    DetectedIssueReference,
    DetectedIssueToken,
)

M = DetectedIssueModel
_I = DetectedIssueIdentifier
_Tk = DetectedIssueToken
_R = DetectedIssueReference

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
        select(literal(1)).where(model.detected_issue_pk == M.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.detected_issue_pk == M.id, *conditions)
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
    return M.detected_issue_id == int(token.code)


def _identified_match(value, modifier, ctx):
    # DetectedIssue.identified[x] is a dateTime or a Period: matched as the range it covers.
    return period_match(M.identified_start, M.identified_end, value)


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


# ── references held as columns: patient / author ─────────────────────────────


def _column_ref(prefix: str, targets: tuple[str, ...]):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on
    the detected_issue row."""
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
        # `modifier` is a target type (author:Practitioner=30001) or None; a bare id with several
        # targets is ambiguous and is rejected by reference_target().
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return or_(ref.is_not(None), ident_value.is_not(None))

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# ── implicated: the shared reference table ───────────────────────────────────


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
    """_include of a reference held as columns: the rows of `resource_type` these issues point at."""

    async def fetch(session, ctx, issues):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(r, id_)
            for r in issues
            if getattr(r, type_) == resource_type and getattr(r, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_reference(param: str, resource_type: str):
    """_include of a reference-table parameter: the rows of `resource_type`."""

    async def fetch(session, ctx, issues):
        ids = select(_R.reference_id).where(
            _R.detected_issue_pk.in_({r.id for r in issues}),
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


def revinclude_issues_via_column(prefix: str, resource_type: str, key):
    """_revinclude=DetectedIssue:patient / :author — issues whose column reference points at one
    of these rows (matched on the public id `key(row)`). Declared on the registry of each target
    type."""

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


def revinclude_issues_via_reference(param: str, resource_type: str, key):
    """_revinclude=DetectedIssue:implicated — issues with a row in the reference table pointing
    at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.detected_issue_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders DetectedIssue rows."""
    from app.fhir.mappers.detected_issue import to_fhir_detected_issue
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "DetectedIssue",
            lambda r: r.detected_issue_id,
            to_fhir_detected_issue,
            "detected-issues",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def detected_issue_search() -> SearchRegistry:
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

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public detected issue id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.detected_issue_id,
            example="540001",
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
        column_ref(
            "author",
            "The provider or device that identified the issue",
            "DetectedIssue.author",
            "author",
            AUTHOR_TYPES,
            "Practitioner/30001",
        ),
        token(
            "code",
            "Issue Category, e.g. drug-drug, duplicate therapy, etc.",
            "DetectedIssue.code",
            "http://terminology.hl7.org/CodeSystem/v3-ActCode|DUPTHPY",
        ),
        SearchParam(
            "identified",
            "date",
            "When identified",
            "DetectedIssue.identified",
            _identified_match,
            lambda ctx: M.identified_start.is_not(None) | M.identified_end.is_not(None),
            sort=lambda: M.identified_start,
            example="ge2026-01-01",
        ),
        SearchParam(
            "identifier",
            "token",
            "Unique id for the detected issue",
            "DetectedIssue.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:issues|DI-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        table_ref(
            "implicated",
            "Problem resource (Reference(Any): needs a type)",
            "DetectedIssue.implicated",
            "Condition/120001",
        ),
        column_ref(
            "patient",
            "Associated patient",
            "DetectedIssue.patient",
            "patient",
            ("Patient",),
            "Patient/10001",
        ),
    ]

    # One include per target type that is a resource here, so `_include=DetectedIssue:author`
    # brings in all of them and `DetectedIssue:author:Practitioner` just the Practitioners.
    author_includes = tuple(
        IncludeTarget("DetectedIssue", "author", t, _include_column("author", t))
        for t in AUTHOR_TYPES
        if t in _MODELED
    )
    implicated_includes = tuple(
        IncludeTarget(
            "DetectedIssue", "implicated", t, _include_reference("implicated", t)
        )
        for t in REFERENCE_TYPES["implicated"]
        if t in _MODELED
    )

    return SearchRegistry(
        resource_type="DetectedIssue",
        params={p.name: p for p in params},
        # Σ elements in the R4 DetectedIssue definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "status",
                "severity",
                "patient",
                "identifiedDateTime",
                "identifiedPeriod",
                "author",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status"}),
        includes=(
            IncludeTarget(
                "DetectedIssue",
                "patient",
                "Patient",
                _include_column("patient", "Patient"),
            ),
            *author_includes,
            *implicated_includes,
        ),
        revincludes=(),
        default_sort=lambda: [M.detected_issue_id.desc()],
    )
