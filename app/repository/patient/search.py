"""
FHIR R4 Patient search parameters
(https://www.hl7.org/fhir/R4/patient.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
patient_search() below. Same arrangement as app.repository.practitioner.search
(names, telecom, address, identifier), app.repository.schedule.search
(multi-target references) and app.repository.practitioner_role.search
(`period_match` over a date held as a range).

Each parameter's SQL reads only the search index (PatientModel's columns and
child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.repository._measure_report_revinclude import (
    column_measure_report_revincludes,
)
from app.repository._communication_request_revinclude import (
    column_communication_request_revincludes,
    reference_communication_request_revincludes,
)
from app.repository._communication_revinclude import (
    column_communication_revincludes,
    reference_communication_revincludes,
)
from app.repository._consent_revinclude import (
    column_consent_revincludes,
    reference_consent_revincludes,
)
from app.repository._flag_revinclude import column_flag_revincludes
from app.repository._task_revinclude import column_task_revincludes
from app.repository._goal_revinclude import column_goal_revincludes
from app.repository._search_targets import MODELED
from app.repository._medication_dispense_revinclude import (
    column_medication_dispense_revincludes,
    reference_medication_dispense_revincludes,
)
from app.repository._medication_administration_revinclude import (
    column_medication_administration_revincludes,
    reference_medication_administration_revincludes,
)
from app.repository._medication_statement_revinclude import (
    column_medication_statement_revincludes,
)
from app.repository._questionnaire_response_revinclude import (
    column_questionnaire_response_revincludes,
)
from app.repository._document_reference_revinclude import (
    column_document_reference_revincludes,
    reference_document_reference_revincludes,
)
from app.repository._episode_of_care_revinclude import (
    column_episode_of_care_revincludes,
)
from app.repository._care_plan_revinclude import (
    column_care_plan_revincludes,
    performer_care_plan_revincludes,
)
from app.repository._schedule_revinclude import actor_schedule_revincludes
from app.repository._care_team_revinclude import (
    column_care_team_revincludes,
    participant_care_team_revincludes,
)
from app.repository._group_revinclude import (
    member_group_revincludes,
)
from app.repository._medication_request_revinclude import (
    column_medication_request_revincludes,
)
from app.repository._service_request_revinclude import (
    column_service_request_revincludes,
    performer_service_request_revincludes,
)
from app.repository._clinical_impression_revinclude import column_impression_revincludes
from app.repository._detected_issue_revinclude import column_issue_revincludes
from app.repository._observation_revinclude import column_observation_revincludes
from app.repository._specimen_revinclude import column_specimen_revincludes
from app.repository._observation_revinclude import reference_observation_revincludes
from app.repository._risk_assessment_revinclude import column_risk_revincludes
from app.repository._appointment_revinclude import participant_revincludes
from app.repository._allergy_intolerance_revinclude import (
    actor_allergy_revincludes,
    patient_allergy_revincludes,
)
from app.repository._condition_revinclude import (
    asserter_condition_revincludes,
    subject_condition_revincludes,
)
from app.repository._procedure_revinclude import (
    performer_procedure_revincludes,
    subject_procedure_revincludes,
)
from app.repository._diagnostic_report_revinclude import subject_report_revincludes
from app.repository._family_member_history_revinclude import patient_history_revincludes
from app.repository._immunization_evaluation_revinclude import (
    column_evaluation_revincludes,
)
from app.repository._immunization_recommendation_revinclude import (
    patient_recommendation_revincludes,
)
from app.repository._immunization_revinclude import column_immunization_revincludes
from app.repository._appointment_response_revinclude import actor_response_revincludes
from app.repository._encounter_revinclude import subject_encounter_revincludes
from app.fhir.search import (
    IncludeTarget,
    MultiValueSort,
    SearchError,
    SearchParam,
    SearchRegistry,
)
from app.fhir.search.sql import (
    array_string_match,
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
from app.models.patient import (
    GENERAL_PRACTITIONER_TYPES,
    LINK_TYPES,
    PatientAddress,
    PatientCommunication,
    PatientIdentifier,
    PatientModel,
    PatientName,
    PatientReference,
    PatientTelecom,
)
from app.schemas.enums import AddressUse, AdministrativeGender

P = PatientModel
_ADDRESS_USE_SYSTEM = "http://hl7.org/fhir/address-use"
_GENDER_SYSTEM = "http://hl7.org/fhir/administrative-gender"

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
    return exists(select(literal(1)).where(model.patient_pk == P.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.patient_pk == P.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(P.updated_at, P.created_at)


# ── _id ──────────────────────────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return P.patient_id == int(token.code)


# ── active / gender / deceased / address-use (tokens) ────────────────────────


def _boolean(value: str, name: str) -> bool:
    token = parse_token(value)
    if token.code not in ("true", "false") or token.system:  # boolean: no code system
        raise SearchError(value, f"'{name}' takes true or false, not '{value}'.")
    return token.code == "true"


def _active_match(value, modifier, ctx):
    return P.active.is_(_boolean(value, "active"))


def _deceased_match(value, modifier, ctx):
    # R4: Patient.deceased.exists() and Patient.deceased != false — so
    # `deceased=false` is everyone who is not marked deceased, including a
    # patient with no deceased[x] at all.
    return (
        P.deceased.is_(True) if _boolean(value, "deceased") else P.deceased.is_not(True)
    )


def _gender_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system is not None and token.system != _GENDER_SYSTEM:
        return (
            false()
        )  # another system, or `|code` (no system) — gender is always coded in its own
    if token.code is None:
        return P.gender.is_not(None)
    try:
        return P.gender == AdministrativeGender(token.code)
    except ValueError:
        return false()  # an unknown code matches nothing (not a failed enum cast)


def _address_use_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system is not None and token.system != _ADDRESS_USE_SYSTEM:
        return false()
    if token.code is None:
        return _exists(PatientAddress, PatientAddress.use.is_not(None))
    try:
        use = AddressUse(token.code)
    except ValueError:
        return false()
    return _exists(PatientAddress, PatientAddress.use == use)


# ── birthdate / death-date (a date held as the range it covers) ──────────────


def _birthdate_match(value, modifier, ctx):
    return period_match(P.birth_date_start, P.birth_date_end, value)


def _death_date_match(value, modifier, ctx):
    return period_match(P.death_date_start, P.death_date_end, value)


# ── names (HumanName) ────────────────────────────────────────────────────────

_N = PatientName


def _name_match(value, modifier, ctx):
    # R4: "may match any of the string fields in the HumanName, including
    # family, given, prefix, suffix, suffix, and/or text".
    return _exists(
        _N,
        or_(
            string_match(_N.text, _N.text_norm, value, modifier),
            string_match(_N.family, _N.family_norm, value, modifier),
            array_string_match(_N.given, _N.given_norm, value, modifier),
            array_string_match(_N.prefix, _N.prefix_norm, value, modifier),
            array_string_match(_N.suffix, _N.suffix_norm, value, modifier),
        ),
    )


def _family_match(value, modifier, ctx):
    return _exists(_N, string_match(_N.family, _N.family_norm, value, modifier))


def _given_match(value, modifier, ctx):
    return _exists(_N, array_string_match(_N.given, _N.given_norm, value, modifier))


def _phonetic_match(value, modifier, ctx):
    from app.core.phonetic import phonetic_codes

    codes = phonetic_codes(value)
    if not codes:
        return false()
    # Every word of the query must sound like some family/given word of one name.
    return _exists(_N, and_(*(_N.phonetic.like(f"% {code} %") for code in codes)))


# ── address ──────────────────────────────────────────────────────────────────

_A = PatientAddress
_ADDRESS_PARTS = {
    "text": (_A.text, _A.text_norm),
    "city": (_A.city, _A.city_norm),
    "district": (_A.district, _A.district_norm),
    "state": (_A.state, _A.state_norm),
    "postal_code": (_A.postal_code, _A.postal_code_norm),
    "country": (_A.country, _A.country_norm),
}


def _address_match(value, modifier, ctx):
    # R4: "may match any of the string fields in the Address, including
    # line, city, district, state, country, postalCode, and/or text".
    return _exists(
        _A,
        or_(
            array_string_match(_A.line, _A.line_norm, value, modifier),
            *(
                string_match(raw, norm, value, modifier)
                for raw, norm in _ADDRESS_PARTS.values()
            ),
        ),
    )


def _address_part(part):
    raw, norm = _ADDRESS_PARTS[part]

    def match(value, modifier, ctx):
        return _exists(_A, string_match(raw, norm, value, modifier))

    def present(ctx):
        return _exists(_A, raw.is_not(None))

    return match, present


# ── identifier / language ────────────────────────────────────────────────────

_I = PatientIdentifier
_C = PatientCommunication


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


def _language_match(value, modifier, ctx):
    return _exists(
        _C,
        coded_token_match(
            _C.system, _C.code, value, modifier, (_C.text_norm, _C.display_norm)
        ),
    )


# ── telecom (ContactPoint) ───────────────────────────────────────────────────

_T = PatientTelecom


def _telecom_match(system: str | None):
    """R4 token search on a ContactPoint: `code` matches `value`, the
    optional `system|` part matches `use`. `phone`/`email` also require
    ContactPoint.system to be that kind."""

    def match(value, modifier, ctx):
        condition = token_condition(_T.use, _T.value, parse_token(value))
        return (
            _exists(_T, condition, _T.system == system)
            if system
            else _exists(_T, condition)
        )

    return match


def _telecom_present(system: str | None):
    def present(ctx):
        return _exists(_T, _T.system == system) if system else _exists(_T)

    return present


# ── organization (0..1 reference held on the row) ────────────────────────────


def _organization_match(value, modifier, ctx):
    if modifier == "identifier":
        return token_condition(
            P.managing_organization_identifier_system,
            P.managing_organization_identifier_value,
            parse_token(value),
        )
    return reference_match(
        P.managing_organization_type,
        P.managing_organization_id,
        P.managing_organization_reference,
        value,
        modifier,
        ctx,
        ("Organization",),
        str,
    )


def _organization_present(ctx):
    return or_(
        P.managing_organization_reference.is_not(None),
        P.managing_organization_identifier_value.is_not(None),
    )


def _organization_chain(target, inner, ctx):
    """`organization.<p>=v`: the managing Organization (same tenant) matches
    any Organization search parameter. The subquery doesn't correlate to the
    outer row — it ranges over the referenced resource."""
    model, id_col = _model("Organization")
    referenced = (
        select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)
    )
    return P.managing_organization_id.in_(referenced)


def _organization_registry():
    return _registry_of("Organization")()


# ── general-practitioner / link (0..*, several possible target types) ────────

_R = PatientReference


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
        # `modifier` is a target type (general-practitioner:Practitioner=30001)
        # or None; a bare id with several targets is ambiguous and is rejected
        # by reference_target(). reference_type is a plain string here.
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
        """`<param>:<Type>.<p>=v`: some referenced resource of that type (same
        tenant) matches `<p>=v`. The subquery doesn't correlate to the outer
        row — it ranges over the referenced resource."""
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


def _include_via_reference(param: str, resource_type: str):
    """_include=Patient:<param>[:Type] — the resources of one type these
    patients point at (only types that are resources on this server)."""

    async def fetch(session, ctx, patients):
        model, id_col = _model(resource_type)
        referenced = select(_R.reference_id).where(
            _R.patient_pk.in_({p.id for p in patients}),
            _R.param == param,
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


async def _include_organization(session, ctx, patients):
    """_include=Patient:organization — the managing organizations."""
    model, id_col = _model("Organization")
    ids = {
        p.managing_organization_id
        for p in patients
        if p.managing_organization_id is not None
    }
    if not ids:
        return []
    return await _fetch(
        session, select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids))
    )


def revinclude_patients_via_reference(param: str, resource_type: str, key):
    """_revinclude=Patient:<param> — patients whose `param` reference of this
    type points at one of these rows (matched on the public id `key(row)`).
    Declared on the registry of each target type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.patient_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(P).where(P.tenant_id == ctx.tenant_id, P.id.in_(pks))
        )

    return fetch


async def revinclude_patients_by_organization(session, ctx, organizations):
    """_revinclude=Patient:organization — patients managed by these organizations."""
    ids = {o.organization_id for o in organizations}
    return await _fetch(
        session,
        select(P).where(
            P.tenant_id == ctx.tenant_id, P.managing_organization_id.in_(ids)
        ),
    )


async def _revinclude_related_persons(session, ctx, patients):
    """_revinclude=RelatedPerson:patient — the people related to these patients."""
    from app.repository.related_person.search import (
        revinclude_related_persons_via_patient,
    )

    return await revinclude_related_persons_via_patient(lambda p: p.patient_id)(
        session, ctx, patients
    )


def _register_kind() -> None:
    """How the search engine identifies and renders Patient rows."""
    from app.fhir.mappers.patient import to_fhir_patient
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind("Patient", lambda p: p.patient_id, to_fhir_patient, "patients")
    )


# ── registry ─────────────────────────────────────────────────────────────────

_city, _city_present = _address_part("city")
_state, _state_present = _address_part("state")
_country, _country_present = _address_part("country")
_postal, _postal_present = _address_part("postal_code")

_STRING = frozenset({"exact", "contains", "missing"})
_TELECOM = frozenset({"not", "missing"})


@cache
def patient_search() -> SearchRegistry:
    _register_kind()

    gp_match, gp_present, gp_chain, gp_sort = _reference_param(
        "general-practitioner", GENERAL_PRACTITIONER_TYPES
    )
    link_match, link_present, link_chain, link_sort = _reference_param(
        "link", LINK_TYPES
    )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public patient id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.patient_id,
            example="10001",
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
            "active",
            "token",
            "Whether the patient record is active",
            "Patient.active",
            _active_match,
            lambda ctx: P.active.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.active,
            example="true",
            modifier_docs={
                "not": "`:not` — active is not this value, or is not recorded at all."
            },
        ),
        SearchParam(
            "address",
            "string",
            "A server defined search that may match any of the string fields in the Address, including line, "
            "city, district, state, country, postalCode, and/or text",
            "Patient.address",
            _address_match,
            lambda ctx: _exists(_A),
            _STRING,
            example="Main St",
        ),
        SearchParam(
            "address-city",
            "string",
            "A city specified in an address",
            "Patient.address.city",
            _city,
            _city_present,
            _STRING,
            sort=lambda: _child_sort(_A.city_norm, _A),
            example="Boston",
        ),
        SearchParam(
            "address-country",
            "string",
            "A country specified in an address",
            "Patient.address.country",
            _country,
            _country_present,
            _STRING,
            sort=lambda: _child_sort(_A.country_norm, _A),
            example="US",
        ),
        SearchParam(
            "address-postalcode",
            "string",
            "A postalCode specified in an address",
            "Patient.address.postalCode",
            _postal,
            _postal_present,
            _STRING,
            sort=lambda: _child_sort(_A.postal_code_norm, _A),
            example="02110",
        ),
        SearchParam(
            "address-state",
            "string",
            "A state specified in an address",
            "Patient.address.state",
            _state,
            _state_present,
            _STRING,
            sort=lambda: _child_sort(_A.state_norm, _A),
            example="MA",
        ),
        SearchParam(
            "address-use",
            "token",
            f"A use code specified in an address (home | work | temp | old | billing; system {_ADDRESS_USE_SYSTEM})",
            "Patient.address.use",
            _address_use_match,
            lambda ctx: _exists(_A, _A.use.is_not(None)),
            frozenset({"not", "missing"}),
            example="home",
        ),
        SearchParam(
            "birthdate",
            "date",
            "The patient's date of birth (a partial date such as 1990 or 1990-05 is matched as the range it covers)",
            "Patient.birthDate",
            _birthdate_match,
            lambda ctx: P.birth_date_start.is_not(None),
            sort=lambda: P.birth_date_start,
            example="ge1990-01-01",
        ),
        SearchParam(
            "death-date",
            "date",
            "The date of death has been provided and satisfies this search value",
            "(Patient.deceased as dateTime)",
            _death_date_match,
            lambda ctx: P.death_date_start.is_not(None),
            sort=lambda: P.death_date_start,
            example="ge2020-01-01",
        ),
        SearchParam(
            "deceased",
            "token",
            "This patient has been marked as deceased, or has a death date entered (true | false)",
            "Patient.deceased.exists() and Patient.deceased != false",
            _deceased_match,
            lambda ctx: P.deceased.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.deceased,
            example="true",
        ),
        SearchParam(
            "email",
            "token",
            "A value in an email contact (ContactPoint.value where system = email)",
            "Patient.telecom.where(system='email')",
            _telecom_match("email"),
            _telecom_present("email"),
            _TELECOM,
            example="peter@example.org",
        ),
        SearchParam(
            "family",
            "string",
            "A portion of the family name of the patient",
            "Patient.name.family",
            _family_match,
            lambda ctx: _exists(_N, _N.family.is_not(None)),
            _STRING,
            sort=lambda: _child_sort(_N.family_norm, _N),
            example="Chalmers",
        ),
        SearchParam(
            "gender",
            "token",
            f"Gender of the patient (male | female | other | unknown; system {_GENDER_SYSTEM})",
            "Patient.gender",
            _gender_match,
            lambda ctx: P.gender.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.gender,
            example="male",
        ),
        SearchParam(
            "general-practitioner",
            "reference",
            "Patient's nominated general practitioner, not the organization that manages the record",
            "Patient.generalPractitioner",
            gp_match,
            gp_present,
            frozenset({"identifier", "missing"}),
            targets=GENERAL_PRACTITIONER_TYPES,
            chain=gp_chain,
            chain_targets={t: _registry_of(t) for t in GENERAL_PRACTITIONER_TYPES},
            sort=gp_sort,
            example="Practitioner/30001",
            modifier_docs={
                "identifier": "`:identifier` — match the logical identifier of a practitioner that has no resource here."
            },
        ),
        SearchParam(
            "given",
            "string",
            "A portion of the given name of the patient",
            "Patient.name.given",
            _given_match,
            lambda ctx: _exists(_N, _N.given.is_not(None)),
            _STRING,
            example="Peter",
        ),
        SearchParam(
            "identifier",
            "token",
            "A patient identifier",
            "Patient.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="http://hospital.example.org/mrn|MRN-12345",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "language",
            "token",
            "Language code (irrespective of use value)",
            "Patient.communication.language",
            _language_match,
            lambda ctx: _exists(_C),
            frozenset({"text", "not", "in", "not-in", "above", "below", "missing"}),
            sort=lambda: _child_sort(_C.code, _C),
            example="urn:ietf:bcp:47|en",
        ),
        SearchParam(
            "link",
            "reference",
            "All patients linked to the given patient",
            "Patient.link.other",
            link_match,
            link_present,
            frozenset({"identifier", "missing"}),
            targets=LINK_TYPES,
            chain=link_chain,
            chain_targets={
                "Patient": _registry_of("Patient"),
                "RelatedPerson": _registry_of("RelatedPerson"),
            },
            sort=link_sort,
            example="Patient/10002",
            modifier_docs={
                "identifier": "`:identifier` — match the logical identifier of a linked patient that has no resource here."
            },
        ),
        SearchParam(
            "name",
            "string",
            "A server defined search that may match any of the string fields in the HumanName, including "
            "family, given, prefix, suffix, and/or text",
            "Patient.name",
            _name_match,
            lambda ctx: _exists(_N),
            _STRING,
            example="Chalmers",
        ),
        SearchParam(
            "organization",
            "reference",
            "The organization that is the custodian of the patient record",
            "Patient.managingOrganization",
            _organization_match,
            _organization_present,
            frozenset({"identifier", "missing"}),
            targets=("Organization",),
            chain=_organization_chain,
            chain_targets={"Organization": _organization_registry},
            sort=lambda: P.managing_organization_id,
            example="Organization/190001",
        ),
        SearchParam(
            "phone",
            "token",
            "A value in a phone contact (ContactPoint.value where system = phone)",
            "Patient.telecom.where(system='phone')",
            _telecom_match("phone"),
            _telecom_present("phone"),
            _TELECOM,
            example="555-9988",
        ),
        SearchParam(
            "phonetic",
            "string",
            "A portion of either family or given name using some kind of phonetic matching algorithm "
            "(American Soundex, word by word; the first letter must match)",
            "Patient.name",
            _phonetic_match,
            lambda ctx: _exists(_N, _N.phonetic.is_not(None)),
            example="Chalmurs",
        ),
        SearchParam(
            "telecom",
            "token",
            "The value in any kind of telecom details of the patient (ContactPoint.value; `use|value` also matches the use)",
            "Patient.telecom",
            _telecom_match(None),
            _telecom_present(None),
            _TELECOM,
            example="555-9988",
        ),
    ]

    return SearchRegistry(
        resource_type="Patient",
        params={p.name: p for p in params},
        # Σ elements in the R4 Patient definition (beyond id/meta/implicitRules);
        # deceased[x] is a choice, so each concrete name is listed.
        summary_elements=frozenset(
            {
                "identifier",
                "active",
                "name",
                "telecom",
                "gender",
                "birthDate",
                "deceasedBoolean",
                "deceasedDateTime",
                "address",
                "managingOrganization",
                "link",
            }
        ),
        # One include per target type, so `_include=Patient:general-practitioner`
        # brings in all of them and `Patient:general-practitioner:Organization`
        # just the Organizations. A RelatedPerson isn't a resource on this server.
        includes=(
            *(
                IncludeTarget(
                    "Patient",
                    "general-practitioner",
                    t,
                    _include_via_reference("general-practitioner", t),
                )
                for t in GENERAL_PRACTITIONER_TYPES
            ),
            IncludeTarget(
                "Patient", "organization", "Organization", _include_organization
            ),
            IncludeTarget(
                "Patient", "link", "Patient", _include_via_reference("link", "Patient")
            ),
            IncludeTarget(
                "Patient",
                "link",
                "RelatedPerson",
                _include_via_reference("link", "RelatedPerson"),
            ),
        ),
        # Patients that link to these patients; the reverses for
        # general-practitioner / organization are declared on Practitioner,
        # PractitionerRole and Organization.
        revincludes=(
            *column_measure_report_revincludes(
                ('subject', 'patient'), "subject", "Patient", lambda x: x.patient_id
            ),
            *column_communication_request_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda x: x.patient_id
            ),
            *column_communication_request_revincludes(
                ("requester",), "requester", "Patient", lambda x: x.patient_id
            ),
            *column_communication_request_revincludes(
                ("sender",), "sender", "Patient", lambda x: x.patient_id
            ),
            *reference_communication_request_revincludes(
                ("recipient",), "Patient", lambda x: x.patient_id
            ),
            *column_communication_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda x: x.patient_id
            ),
            *column_communication_revincludes(
                ("sender",), "sender", "Patient", lambda x: x.patient_id
            ),
            *reference_communication_revincludes(
                ("recipient",), "Patient", lambda x: x.patient_id
            ),
            *column_consent_revincludes(
                ("patient",), "patient", "Patient", lambda x: x.patient_id
            ),
            *reference_consent_revincludes(
                ("consentor", "actor"), "Patient", lambda x: x.patient_id
            ),
            *column_flag_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda x: x.patient_id
            ),
            *column_flag_revincludes(
                ("author",), "author", "Patient", lambda x: x.patient_id
            ),
            *column_task_revincludes(
                ("subject", "patient"), "for", "Patient", lambda x: x.patient_id
            ),
            *column_task_revincludes(
                ("owner",), "owner", "Patient", lambda x: x.patient_id
            ),
            *column_task_revincludes(
                ("requester",), "requester", "Patient", lambda x: x.patient_id
            ),
            *column_medication_dispense_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda x: x.patient_id
            ),
            *reference_medication_dispense_revincludes(
                "performer", "Patient", lambda x: x.patient_id
            ),
            *reference_medication_dispense_revincludes(
                "receiver", "Patient", lambda x: x.patient_id
            ),
            *column_medication_administration_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda x: x.patient_id
            ),
            *reference_medication_administration_revincludes(
                "performer", "Patient", lambda x: x.patient_id
            ),
            *column_medication_statement_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda x: x.patient_id
            ),
            *column_medication_statement_revincludes(
                ("source",), "source", "Patient", lambda x: x.patient_id
            ),
            *column_questionnaire_response_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda x: x.patient_id
            ),
            *column_questionnaire_response_revincludes(
                ("author",), "author", "Patient", lambda x: x.patient_id
            ),
            *column_questionnaire_response_revincludes(
                ("source",), "source", "Patient", lambda x: x.patient_id
            ),
            *column_document_reference_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda x: x.patient_id
            ),
            *reference_document_reference_revincludes(
                "author", "Patient", lambda x: x.patient_id
            ),
            *column_episode_of_care_revincludes(
                "patient", "patient", "Patient", lambda x: x.patient_id
            ),
            *column_care_plan_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda x: x.patient_id
            ),
            *performer_care_plan_revincludes("Patient", lambda x: x.patient_id),
            *column_care_team_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda p: p.patient_id
            ),
            *participant_care_team_revincludes("Patient", lambda p: p.patient_id),
            *column_goal_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda p: p.patient_id
            ),
            *actor_schedule_revincludes("Patient", lambda p: p.patient_id),
            *member_group_revincludes("Patient", lambda p: p.patient_id),
            *column_medication_request_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda p: p.patient_id
            ),
            *column_medication_request_revincludes(
                ("requester",), "requester", "Patient", lambda p: p.patient_id
            ),
            *column_medication_request_revincludes(
                ("intended-performer",), "performer", "Patient", lambda p: p.patient_id
            ),
            *column_service_request_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda p: p.patient_id
            ),
            *column_service_request_revincludes(
                ("requester",), "requester", "Patient", lambda p: p.patient_id
            ),
            *performer_service_request_revincludes("Patient", lambda p: p.patient_id),
            *participant_revincludes(
                "Patient", lambda p: p.patient_id, ("actor", "patient")
            ),
            *actor_response_revincludes(
                "Patient", lambda p: p.patient_id, ("actor", "patient")
            ),
            *subject_encounter_revincludes(lambda p: p.patient_id),
            *patient_allergy_revincludes(lambda p: p.patient_id),
            *subject_condition_revincludes(lambda p: p.patient_id),
            *asserter_condition_revincludes("Patient", lambda p: p.patient_id),
            *subject_procedure_revincludes(lambda p: p.patient_id),
            *subject_report_revincludes(
                "Patient", lambda p: p.patient_id, ("subject", "patient")
            ),
            *column_immunization_revincludes(
                "patient", "patient", "Patient", lambda p: p.patient_id
            ),
            *patient_recommendation_revincludes(lambda p: p.patient_id),
            *patient_history_revincludes(lambda p: p.patient_id),
            *column_risk_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda p: p.patient_id
            ),
            *column_impression_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda p: p.patient_id
            ),
            *column_issue_revincludes(
                ("patient",), "patient", "Patient", lambda p: p.patient_id
            ),
            *column_observation_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda p: p.patient_id
            ),
            *column_specimen_revincludes(
                ("subject", "patient"), "subject", "Patient", lambda p: p.patient_id
            ),
            *reference_observation_revincludes(
                "performer", "Patient", lambda p: p.patient_id
            ),
            *column_evaluation_revincludes(
                "patient", "patient", "Patient", lambda p: p.patient_id
            ),
            *performer_procedure_revincludes("Patient", lambda p: p.patient_id),
            *actor_allergy_revincludes("Patient", lambda p: p.patient_id),
            IncludeTarget(
                "RelatedPerson",
                "patient",
                "Patient",
                _revinclude_related_persons,
                reverse=True,
            ),
            IncludeTarget(
                "Patient",
                "link",
                "Patient",
                revinclude_patients_via_reference(
                    "link", "Patient", lambda p: p.patient_id
                ),
                reverse=True,
            ),
        ),
        default_sort=lambda: [P.patient_id.desc()],
    )
