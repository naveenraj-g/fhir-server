"""
FHIR R4 DocumentReference search parameters
(https://www.hl7.org/fhir/R4/documentreference.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`, `_include` /
`_revinclude`, and the OpenAPI docs all come from document_reference_search() below. Same
arrangement as app.repository.care_team.search (single references held as columns, shared token
and reference tables) plus `relatesTo` and `content` held in their own tables (one row per entry),
which is what lets the `relationship` composite pair a target with its code, and `location` /
`contenttype` / `language` / `format` read the same attachment.

Each parameter's SQL reads only the search index (DocumentReferenceModel's columns and child
tables, see its docstring) - never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.composite import split_composite
from app.fhir.search.sql import (
    coded_token_match,
    date_match,
    period_match,
    reference_match,
    string_match,
    token_condition,
    token_match,
    token_text_match,
    uri_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.models.document_reference import (
    AUTHENTICATOR_TYPES,
    CUSTODIAN_TYPES,
    REFERENCE_TYPES,
    RELATES_TO_TYPES,
    RELATION_SYSTEM,
    SUBJECT_TYPES,
    DocumentReferenceContent,
    DocumentReferenceIdentifier,
    DocumentReferenceModel,
    DocumentReferenceReference,
    DocumentReferenceRelatesTo,
    DocumentReferenceStatus,
    DocumentReferenceToken,
    DocumentRelationshipType,
)

M = DocumentReferenceModel
_I = DocumentReferenceIdentifier
_Tk = DocumentReferenceToken
_R = DocumentReferenceReference
_Rel = DocumentReferenceRelatesTo
_C = DocumentReferenceContent

# DocumentReference.status is a `code` from the R4 document-reference-status system.
_STATUS_SYSTEM = "http://hl7.org/fhir/document-reference-status"

# Reference targets that are searchable resources on this server: the model to join for chaining
# / `_include`, and its registry.
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
    "EpisodeOfCare": (
        "app.models.episode_of_care",
        "EpisodeOfCareModel",
        "episode_of_care_id",
        "app.repository.episode_of_care.search",
        "episode_of_care_search",
    ),
    "DocumentReference": (
        "app.models.document_reference",
        "DocumentReferenceModel",
        "document_reference_id",
        "app.repository.document_reference.search",
        "document_reference_search",
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
        select(literal(1)).where(model.document_reference_pk == M.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.document_reference_pk == M.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(M.updated_at, M.created_at)


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition. Does not correlate to the
    outer row - it ranges over the referenced resource."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return M.document_reference_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the document-reference-status system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an unknown code matches
    nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == DocumentReferenceStatus(token.code)
    except ValueError:
        return false()


def _date_match(value, modifier, ctx):
    # DocumentReference.date is an instant.
    return date_match(M.date, value)


def _period_match(value, modifier, ctx):
    # context.period is a Period: matched as the range it covers (a document with no period never
    # matches).
    return period_match(M.context_period_start, M.context_period_end, value)


def _description_match(value, modifier, ctx):
    return string_match(M.description, M.description_norm, value, modifier)


def _identifier_param(model):
    """(match, present, sort) for an Identifier search held in one identifier-shaped table
    (`identifier`: masterIdentifier and every identifier)."""

    def match(value, modifier, ctx):
        if modifier == "text":
            return _exists(
                model,
                token_text_match(
                    (model.type_text_norm, model.type_display_norm), value
                ),
            )
        if modifier == "of-type":
            type_system, type_code, ident = parse_of_type(value)
            return _exists(
                model,
                model.type_system == type_system,
                model.type_code == type_code,
                model.value == ident,
            )
        return _exists(model, token_match(model.system, model.value, value))

    def present(ctx):
        return _exists(model)

    def sort():
        return _child_sort(model.value, model)

    return match, present, sort


def _token_param(param: str):
    """(match, present, sort) for one of the token parameters held in the shared token table,
    selected by its `param` value."""

    def match(value, modifier, ctx):
        return _exists(
            _Tk,
            _Tk.param == param,
            coded_token_match(
                _Tk.system,
                _Tk.code,
                value,
                modifier,
                (_Tk.text_norm, _Tk.display_norm),
            ),
        )

    def present(ctx):
        return _exists(_Tk, _Tk.param == param)

    def sort():
        return _child_sort(_Tk.code, _Tk, _Tk.param == param)

    return match, present, sort


# ── references held as columns: subject / patient / authenticator / custodian ─


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    document_reference row. `narrowed` restricts a multi-target element to one type (`patient` is
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
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return and_(or_(ref.is_not(None), ident_value.is_not(None)), *type_filter)

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# ── author / encounter / related: one row per Reference in the shared reference table ──


def _reference_param(param: str):
    """(match, present, chain, sort) for one of the reference parameters held in the shared
    reference table, selected by its `param` value."""
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


# ── relatesTo: relatesto / relation / relationship (one row per entry) ────────


def _relatesto_target(value, modifier, ctx):
    """The condition on one relates_to row for a `relatesto` value (a bare id or `Type/id`, an
    absolute URL, or `:identifier`)."""
    if modifier == "identifier":
        return token_condition(
            _Rel.target_identifier_system,
            _Rel.target_identifier_value,
            parse_token(value),
        )
    return reference_match(
        _Rel.target_type,
        _Rel.target_id,
        _Rel.target_reference,
        value,
        modifier,
        ctx,
        RELATES_TO_TYPES,
        str,
    )


def _relation_condition(value: str):
    """The condition on one relates_to row for a `relation` value: `code` or `system|code`
    (document-relationship-type); another system, `|code` (no system) or an unknown code matches
    nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != RELATION_SYSTEM:
        return false()
    if token.code is None:
        return _Rel.code.is_not(None)
    try:
        return _Rel.code == DocumentRelationshipType(token.code)
    except ValueError:
        return false()


def _relatesto_param():
    def match(value, modifier, ctx):
        return _exists(_Rel, _relatesto_target(value, modifier, ctx))

    def present(ctx):
        return _exists(
            _Rel,
            or_(
                _Rel.target_reference.is_not(None),
                _Rel.target_identifier_value.is_not(None),
            ),
        )

    def chain(target, inner, ctx):
        return _exists(
            _Rel,
            _Rel.target_type == target,
            _Rel.target_id.in_(_referenced(target, inner, ctx)),
        )

    return match, present, chain, lambda: _child_sort(_Rel.target_id, _Rel)


def _relation_match(value, modifier, ctx):
    return _exists(_Rel, _relation_condition(value))


def _relationship_match(value, modifier, ctx):
    """`relationship=<relatesto>$<relation>`: some relatesTo entry whose target matches the first
    part *and* whose code matches the second - both on the same row, which is what stops the target
    of one entry pairing with the code of another (R4 defines the composite as the two component
    parameters `relatesto` and `relation`, in that order)."""
    target_part, relation_part = split_composite(value, 2)
    return _exists(
        _Rel,
        _relatesto_target(target_part, None, ctx),
        _relation_condition(relation_part),
    )


# ── content: contenttype / language / location / format ──────────────────────


def _code_only_match(column):
    """A token search over a `code` element held as a plain string (Attachment.contentType,
    Attachment.language): it matches the code only (exact, case-sensitive), so a `system|code`
    value (a code of this kind has no system) never matches."""

    def match(value, modifier, ctx):
        token = parse_token(value)
        if token.system is not None or token.code is None:
            return false()
        return _exists(_C, column == token.code)

    return match


def _location_match(value, modifier, ctx):
    return _exists(_C, uri_match(_C.url, value, modifier))


def _format_match(value, modifier, ctx):
    return _exists(
        _C,
        coded_token_match(
            _C.format_system,
            _C.format_code,
            value,
            modifier,
            (_C.format_display_norm, _C.format_display_norm),
        ),
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
    """_include of a reference held as columns: the rows of `resource_type` these documents point
    at."""

    async def fetch(session, ctx, documents):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(r, id_)
            for r in documents
            if getattr(r, type_) == resource_type and getattr(r, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_reference(param: str, resource_type: str):
    """_include of a reference held in the shared reference table: the rows of `resource_type`
    these documents' `param` references point at."""

    async def fetch(session, ctx, documents):
        ids = select(_R.reference_id).where(
            _R.document_reference_pk.in_({r.id for r in documents}),
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


def _include_relatesto(documents_ctx_unused=None):
    async def fetch(session, ctx, documents):
        ids = select(_Rel.target_id).where(
            _Rel.document_reference_pk.in_({r.id for r in documents}),
            _Rel.target_type == "DocumentReference",
            _Rel.target_id.is_not(None),
        )
        return await _load(
            session,
            ctx,
            "DocumentReference",
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


def revinclude_documents_via_column(prefix: str, resource_type: str, key):
    """_revinclude=DocumentReference:subject / :patient / :authenticator / :custodian - documents
    whose column reference points at one of these rows (matched on the public id `key(row)`).
    Declared on the registry of each target type."""

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


def revinclude_documents_via_reference(param: str, resource_type: str, key):
    """_revinclude=DocumentReference:author / :encounter - documents with a reference row of
    `param` pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.document_reference_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def revinclude_documents_via_relatesto(key):
    """_revinclude=DocumentReference:relatesto - documents whose relatesTo names one of these
    documents."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_Rel.document_reference_pk).where(
            _Rel.target_type == "DocumentReference", _Rel.target_id.in_(ids)
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders DocumentReference rows."""
    from app.fhir.mappers.document_reference import to_fhir_document_reference
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "DocumentReference",
            lambda r: r.document_reference_id,
            to_fhir_document_reference,
            "document-references",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER = frozenset({"text", "not", "of-type", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}
_TEXT_DOC = {
    "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
}


@cache
def document_reference_search() -> SearchRegistry:
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

    def code_token(name, description, expression, column, example):
        return SearchParam(
            name,
            "token",
            description,
            expression,
            _code_only_match(column),
            lambda ctx: _exists(_C, column.is_not(None)),
            frozenset({"not", "missing"}),
            sort=lambda: _child_sort(column, _C),
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
        match, present, chain, sort = _reference_param(name)
        targets = REFERENCE_TYPES[name]
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

    identifier_match, identifier_present, identifier_sort = _identifier_param(_I)
    relatesto_match, relatesto_present, relatesto_chain, relatesto_sort = (
        _relatesto_param()
    )
    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public document reference id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.document_reference_id,
            example="320001",
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
            "author",
            "Who and/or what authored the document",
            "DocumentReference.author",
            "Practitioner/30001",
        ),
        column_ref(
            "authenticator",
            "Who/what authenticated the document",
            "DocumentReference.authenticator",
            "authenticator",
            AUTHENTICATOR_TYPES,
            "Practitioner/30001",
        ),
        token(
            "category",
            "Categorization of document",
            "DocumentReference.category",
            "http://loinc.org|LP173421-1",
        ),
        code_token(
            "contenttype",
            "Mime type of the content, may include charset information",
            "DocumentReference.content.attachment.contentType",
            _C.content_type,
            "application/pdf",
        ),
        column_ref(
            "custodian",
            "Organization which maintains the document",
            "DocumentReference.custodian",
            "custodian",
            CUSTODIAN_TYPES,
            "Organization/190001",
        ),
        SearchParam(
            "date",
            "date",
            "When this document reference was created",
            "DocumentReference.date",
            _date_match,
            lambda ctx: M.date.is_not(None),
            sort=lambda: M.date,
            example="ge2026-01-01",
        ),
        SearchParam(
            "description",
            "string",
            "Human-readable description",
            "DocumentReference.description",
            _description_match,
            lambda ctx: M.description.is_not(None),
            frozenset({"exact", "contains", "missing"}),
            sort=lambda: M.description_norm,
            example="Discharge",
        ),
        table_ref(
            "encounter",
            "Context of the document content",
            "DocumentReference.context.encounter",
            "Encounter/20001",
        ),
        token(
            "event",
            "Main clinical acts documented",
            "DocumentReference.context.event",
            "http://terminology.hl7.org/CodeSystem/v3-ActCode|AMB",
        ),
        token(
            "facility",
            "Kind of facility where patient was seen",
            "DocumentReference.context.facilityType",
            "http://snomed.info/sct|22232009",
        ),
        SearchParam(
            "format",
            "token",
            "Format/content rules for the document",
            "DocumentReference.content.format",
            _format_match,
            lambda ctx: _exists(_C, _C.format_code.is_not(None)),
            _TOKEN,
            sort=lambda: _child_sort(_C.format_code, _C),
            example="urn:ihe:pcc:handp:2008",
        ),
        SearchParam(
            "identifier",
            "token",
            "Master Version Specific Identifier (masterIdentifier and identifier)",
            "DocumentReference.masterIdentifier | DocumentReference.identifier",
            identifier_match,
            identifier_present,
            _IDENTIFIER,
            sort=identifier_sort,
            example="urn:documents|DOC-1",
            modifier_docs=_TEXT_DOC,
        ),
        code_token(
            "language",
            "Human language of the content (BCP-47)",
            "DocumentReference.content.attachment.language",
            _C.language,
            "en",
        ),
        SearchParam(
            "location",
            "uri",
            "Uri where the data can be found",
            "DocumentReference.content.attachment.url",
            _location_match,
            lambda ctx: _exists(_C, _C.url.is_not(None)),
            frozenset({"above", "below", "missing"}),
            sort=lambda: _child_sort(_C.url, _C),
            example="https://documents.example.org/doc-1001.pdf",
            modifier_docs={
                "below": "`:below` — stored URLs that start with the value.",
                "above": "`:above` — stored URLs that are a prefix of the value.",
            },
        ),
        column_ref(
            "patient",
            "Who/what is the subject of the document",
            "DocumentReference.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        SearchParam(
            "period",
            "date",
            "Time of service that is being documented",
            "DocumentReference.context.period",
            _period_match,
            lambda ctx: (
                M.context_period_start.is_not(None) | M.context_period_end.is_not(None)
            ),
            sort=lambda: M.context_period_start,
            example="ge2026-01-01",
        ),
        table_ref(
            "related",
            "Related identifiers or resources (Reference(Any): needs a type)",
            "DocumentReference.context.related",
            "Condition/120001",
        ),
        SearchParam(
            "relatesto",
            "reference",
            "Target of the relationship",
            "DocumentReference.relatesTo.target",
            relatesto_match,
            relatesto_present,
            _REFERENCE,
            targets=RELATES_TO_TYPES,
            chain=relatesto_chain,
            chain_targets={"DocumentReference": _registry_of("DocumentReference")},
            sort=relatesto_sort,
            example="DocumentReference/320001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        SearchParam(
            "relation",
            "token",
            f"replaces | transforms | signs | appends (system {RELATION_SYSTEM})",
            "DocumentReference.relatesTo.code",
            _relation_match,
            lambda ctx: _exists(_Rel, _Rel.code.is_not(None)),
            frozenset({"not", "missing"}),
            sort=lambda: _child_sort(_Rel.code, _Rel),
            example="replaces",
        ),
        SearchParam(
            "relationship",
            "composite",
            "Combination of relation and relatesTo: `<relatesto>$<relation>`, e.g. "
            "`DocumentReference/320001$replaces`",
            "DocumentReference.relatesTo",
            _relationship_match,
            lambda ctx: _exists(_Rel),
            frozenset(),
            example="DocumentReference/320001$replaces",
        ),
        token(
            "security-label",
            "Document security-tags",
            "DocumentReference.securityLabel",
            "http://terminology.hl7.org/CodeSystem/v3-Confidentiality|N",
        ),
        token(
            "setting",
            "Additional details about where the content was created (e.g. clinical specialty)",
            "DocumentReference.context.practiceSetting",
            "http://snomed.info/sct|408443003",
        ),
        SearchParam(
            "status",
            "token",
            f"current | superseded | entered-in-error (system {_STATUS_SYSTEM})",
            "DocumentReference.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="current",
        ),
        column_ref(
            "subject",
            "Who/what is the subject of the document",
            "DocumentReference.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
        token(
            "type",
            "Kind of document (LOINC if possible)",
            "DocumentReference.type",
            "http://loinc.org|34133-9",
        ),
    ]

    # One include per target type that is a resource here, so `_include=DocumentReference:subject`
    # brings in all of them and `DocumentReference:subject:Group` just the Groups.
    def column_includes(param, prefix, targets):
        return tuple(
            IncludeTarget("DocumentReference", param, t, _include_column(prefix, t))
            for t in targets
            if t in _MODELED
        )

    def table_includes(param):
        return tuple(
            IncludeTarget("DocumentReference", param, t, _include_reference(param, t))
            for t in REFERENCE_TYPES[param]
            if t in _MODELED
        )

    return SearchRegistry(
        resource_type="DocumentReference",
        params={p.name: p for p in params},
        # Σ elements in the R4 DocumentReference definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "masterIdentifier",
                "identifier",
                "status",
                "docStatus",
                "type",
                "category",
                "subject",
                "date",
                "author",
                "relatesTo",
                "description",
                "securityLabel",
                "content",
                "context",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "content"}),
        includes=(
            IncludeTarget(
                "DocumentReference",
                "patient",
                "Patient",
                _include_column("subject", "Patient"),
            ),
            *column_includes("subject", "subject", SUBJECT_TYPES),
            *column_includes("authenticator", "authenticator", AUTHENTICATOR_TYPES),
            *column_includes("custodian", "custodian", CUSTODIAN_TYPES),
            *table_includes("author"),
            *table_includes("encounter"),
            *table_includes("related"),
            IncludeTarget(
                "DocumentReference",
                "relatesto",
                "DocumentReference",
                _include_relatesto(),
            ),
        ),
        # A document can name another document as the target of its relatesTo.
        revincludes=(
            IncludeTarget(
                "DocumentReference",
                "relatesto",
                "DocumentReference",
                revinclude_documents_via_relatesto(lambda r: r.document_reference_id),
                reverse=True,
            ),
        ),
        default_sort=lambda: [M.document_reference_id.desc()],
    )
