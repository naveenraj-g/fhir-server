"""
FHIR R4 RelatedPerson search parameters
(https://www.hl7.org/fhir/R4/relatedperson.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from
related_person_search() below. Same arrangement as app.repository.patient.search
(names, telecom, address, identifier, a birth date held as a range, a reference
held as columns on the row).

Each parameter's SQL reads only the search index (RelatedPersonModel's columns
and child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.repository._communication_revinclude import (
    column_communication_revincludes,
    reference_communication_revincludes,
)
from app.repository._consent_revinclude import reference_consent_revincludes
from app.repository._task_revinclude import column_task_revincludes
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
from app.repository._medication_dispense_revinclude import (
    reference_medication_dispense_revincludes,
)
from app.repository._medication_administration_revinclude import (
    reference_medication_administration_revincludes,
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
from app.repository._care_plan_revinclude import performer_care_plan_revincludes
from app.repository._schedule_revinclude import actor_schedule_revincludes
from app.repository._care_team_revinclude import participant_care_team_revincludes
from app.repository._group_revinclude import (
    managing_entity_group_revincludes,
    member_group_revincludes,
)
from app.repository._medication_request_revinclude import (
    column_medication_request_revincludes,
)
from app.repository._service_request_revinclude import (
    column_service_request_revincludes,
    performer_service_request_revincludes,
    specimen_service_request_revincludes,
)
from app.models.related_person import (
    RelatedPersonAddress,
    RelatedPersonIdentifier,
    RelatedPersonModel,
    RelatedPersonName,
    RelatedPersonRelationship,
    RelatedPersonTelecom,
)
from app.repository._appointment_revinclude import participant_revincludes
from app.repository._allergy_intolerance_revinclude import actor_allergy_revincludes
from app.repository._condition_revinclude import asserter_condition_revincludes
from app.repository._procedure_revinclude import performer_procedure_revincludes
from app.repository._appointment_response_revinclude import actor_response_revincludes
from app.repository._encounter_revinclude import participant_encounter_revincludes
from app.repository._observation_revinclude import reference_observation_revincludes
from app.schemas.enums import AddressUse, AdministrativeGender

R = RelatedPersonModel
_ADDRESS_USE_SYSTEM = "http://hl7.org/fhir/address-use"
_GENDER_SYSTEM = "http://hl7.org/fhir/administrative-gender"


def _patient_model():
    from app.models.patient import PatientModel

    return PatientModel, PatientModel.patient_id


def _patient_registry():
    from app.repository.patient.search import patient_search

    return patient_search()


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(
        select(literal(1)).where(model.related_person_pk == R.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.related_person_pk == R.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(R.updated_at, R.created_at)


# ── _id ──────────────────────────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return R.related_person_id == int(token.code)


# ── active / gender / address-use (tokens) ───────────────────────────────────


def _active_match(value, modifier, ctx):
    token = parse_token(value)
    if token.code not in ("true", "false") or token.system:  # boolean: no code system
        raise SearchError(value, f"'active' takes true or false, not '{value}'.")
    return R.active.is_(token.code == "true")


def _gender_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system is not None and token.system != _GENDER_SYSTEM:
        return (
            false()
        )  # another system, or `|code` (no system) — gender is always coded in its own
    if token.code is None:
        return R.gender.is_not(None)
    try:
        return R.gender == AdministrativeGender(token.code)
    except ValueError:
        return false()  # an unknown code matches nothing (not a failed enum cast)


_A = RelatedPersonAddress


def _address_use_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system is not None and token.system != _ADDRESS_USE_SYSTEM:
        return false()
    if token.code is None:
        return _exists(_A, _A.use.is_not(None))
    try:
        use = AddressUse(token.code)
    except ValueError:
        return false()
    return _exists(_A, _A.use == use)


# ── birthdate (a date held as the range it covers) ───────────────────────────


def _birthdate_match(value, modifier, ctx):
    return period_match(R.birth_date_start, R.birth_date_end, value)


# ── names (HumanName) ────────────────────────────────────────────────────────

_N = RelatedPersonName


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


def _phonetic_match(value, modifier, ctx):
    from app.core.phonetic import phonetic_codes

    codes = phonetic_codes(value)
    if not codes:
        return false()
    # Every word of the query must sound like some family/given word of one name.
    return _exists(_N, and_(*(_N.phonetic.like(f"% {code} %") for code in codes)))


# ── address ──────────────────────────────────────────────────────────────────

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


# ── identifier / relationship ────────────────────────────────────────────────

_I = RelatedPersonIdentifier
_Rel = RelatedPersonRelationship


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


def _relationship_match(value, modifier, ctx):
    return _exists(
        _Rel,
        coded_token_match(
            _Rel.system, _Rel.code, value, modifier, (_Rel.text_norm, _Rel.display_norm)
        ),
    )


# ── telecom (ContactPoint) ───────────────────────────────────────────────────

_T = RelatedPersonTelecom


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


# ── patient (1..1 reference held on the row) ─────────────────────────────────


def _patient_match(value, modifier, ctx):
    if modifier == "identifier":
        return token_condition(
            R.patient_identifier_system, R.patient_identifier_value, parse_token(value)
        )
    return reference_match(
        R.patient_type,
        R.patient_id,
        R.patient_reference,
        value,
        modifier,
        ctx,
        ("Patient",),
        str,
    )


def _patient_present(ctx):
    return or_(
        R.patient_reference.is_not(None), R.patient_identifier_value.is_not(None)
    )


def _patient_chain(target, inner, ctx):
    """`patient.<p>=v`: the Patient (same tenant) matches any Patient search
    parameter. The subquery doesn't correlate to the outer row — it ranges over
    the referenced resource."""
    model, id_col = _patient_model()
    referenced = (
        select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)
    )
    return and_(R.patient_type == "Patient", R.patient_id.in_(referenced))


# ── _include / _revinclude ───────────────────────────────────────────────────


async def _include_patient(session, ctx, related_persons):
    """_include=RelatedPerson:patient — the patients these people relate to."""
    ids = {
        r.patient_id
        for r in related_persons
        if r.patient_type == "Patient" and r.patient_id is not None
    }
    if not ids:
        return []
    model, id_col = _patient_model()
    return list(
        (
            await session.execute(
                select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids))
            )
        ).scalars()
    )


def revinclude_related_persons_via_patient(key):
    """_revinclude=RelatedPerson:patient — people related to one of these
    patients (matched on the public id `key(row)`). Declared on Patient."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        stmt = select(R).where(
            R.tenant_id == ctx.tenant_id,
            R.patient_type == "Patient",
            R.patient_id.in_(ids),
        )
        return list((await session.execute(stmt)).scalars())

    return fetch


def _revinclude_patients_linking(session_key):
    """_revinclude=Patient:link — patients whose `link.other` is one of these
    related persons."""

    async def fetch(session, ctx, rows):
        from app.repository.patient.search import revinclude_patients_via_reference

        return await revinclude_patients_via_reference(
            "link", "RelatedPerson", session_key
        )(session, ctx, rows)

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders RelatedPerson rows."""
    from app.fhir.mappers.related_person import to_fhir_related_person
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "RelatedPerson",
            lambda r: r.related_person_id,
            to_fhir_related_person,
            "related-persons",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_city, _city_present = _address_part("city")
_state, _state_present = _address_part("state")
_country, _country_present = _address_part("country")
_postal, _postal_present = _address_part("postal_code")

_STRING = frozenset({"exact", "contains", "missing"})
_TELECOM = frozenset({"not", "missing"})


@cache
def related_person_search() -> SearchRegistry:
    _register_kind()

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public related person id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: R.related_person_id,
            example="300001",
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
            "Indicates if the related person record is active",
            "RelatedPerson.active",
            _active_match,
            lambda ctx: R.active.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: R.active,
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
            "RelatedPerson.address",
            _address_match,
            lambda ctx: _exists(_A),
            _STRING,
            example="Main St",
        ),
        SearchParam(
            "address-city",
            "string",
            "A city specified in an address",
            "RelatedPerson.address.city",
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
            "RelatedPerson.address.country",
            _country,
            _country_present,
            _STRING,
            sort=lambda: _child_sort(_A.country_norm, _A),
            example="US",
        ),
        SearchParam(
            "address-postalcode",
            "string",
            "A postal code specified in an address",
            "RelatedPerson.address.postalCode",
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
            "RelatedPerson.address.state",
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
            "RelatedPerson.address.use",
            _address_use_match,
            lambda ctx: _exists(_A, _A.use.is_not(None)),
            frozenset({"not", "missing"}),
            example="home",
        ),
        SearchParam(
            "birthdate",
            "date",
            "The Related Person's date of birth (a partial date such as 1990 or 1990-05 is matched as the range it covers)",
            "RelatedPerson.birthDate",
            _birthdate_match,
            lambda ctx: R.birth_date_start.is_not(None),
            sort=lambda: R.birth_date_start,
            example="ge1990-01-01",
        ),
        SearchParam(
            "email",
            "token",
            "A value in an email contact (ContactPoint.value where system = email)",
            "RelatedPerson.telecom.where(system='email')",
            _telecom_match("email"),
            _telecom_present("email"),
            _TELECOM,
            example="peter@example.org",
        ),
        SearchParam(
            "gender",
            "token",
            f"Gender of the related person (male | female | other | unknown; system {_GENDER_SYSTEM})",
            "RelatedPerson.gender",
            _gender_match,
            lambda ctx: R.gender.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: R.gender,
            example="female",
        ),
        SearchParam(
            "identifier",
            "token",
            "An Identifier of the RelatedPerson",
            "RelatedPerson.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:related-persons|RP-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "name",
            "string",
            "A server defined search that may match any of the string fields in the HumanName, including "
            "family, given, prefix, suffix, and/or text",
            "RelatedPerson.name",
            _name_match,
            lambda ctx: _exists(_N),
            _STRING,
            sort=lambda: _child_sort(_N.family_norm, _N),
            example="Chalmers",
        ),
        SearchParam(
            "patient",
            "reference",
            "The patient this related person is related to",
            "RelatedPerson.patient",
            _patient_match,
            _patient_present,
            frozenset({"identifier", "missing"}),
            targets=("Patient",),
            chain=_patient_chain,
            chain_targets={"Patient": _patient_registry},
            sort=lambda: R.patient_id,
            example="Patient/10001",
        ),
        SearchParam(
            "phone",
            "token",
            "A value in a phone contact (ContactPoint.value where system = phone)",
            "RelatedPerson.telecom.where(system='phone')",
            _telecom_match("phone"),
            _telecom_present("phone"),
            _TELECOM,
            example="555-9988",
        ),
        SearchParam(
            "phonetic",
            "string",
            "A portion of name using some kind of phonetic matching algorithm "
            "(American Soundex, word by word; the first letter must match)",
            "RelatedPerson.name",
            _phonetic_match,
            lambda ctx: _exists(_N, _N.phonetic.is_not(None)),
            example="Chalmurs",
        ),
        SearchParam(
            "relationship",
            "token",
            "The relationship between the patient and the relatedperson",
            "RelatedPerson.relationship",
            _relationship_match,
            lambda ctx: _exists(_Rel),
            frozenset({"text", "not", "in", "not-in", "above", "below", "missing"}),
            sort=lambda: _child_sort(_Rel.code, _Rel),
            example="http://terminology.hl7.org/CodeSystem/v3-RoleCode|MTH",
        ),
        SearchParam(
            "telecom",
            "token",
            "The value in any kind of contact (ContactPoint.value; `use|value` also matches the use)",
            "RelatedPerson.telecom",
            _telecom_match(None),
            _telecom_present(None),
            _TELECOM,
            example="555-9988",
        ),
    ]

    return SearchRegistry(
        resource_type="RelatedPerson",
        params={p.name: p for p in params},
        # Σ elements in the R4 RelatedPerson definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "active",
                "patient",
                "relationship",
                "name",
                "telecom",
                "gender",
                "birthDate",
                "address",
            }
        ),
        mandatory_elements=frozenset({"patient"}),
        includes=(
            IncludeTarget("RelatedPerson", "patient", "Patient", _include_patient),
        ),
        # What points at a RelatedPerson: Appointment / AppointmentResponse actors, Encounter
        # participants and Patient.link.
        revincludes=(
            *column_communication_revincludes(
                ("sender",), "sender", "RelatedPerson", lambda x: x.related_person_id
            ),
            *reference_communication_revincludes(
                ("recipient",), "RelatedPerson", lambda x: x.related_person_id
            ),
            *reference_consent_revincludes(
                ("consentor", "actor"), "RelatedPerson", lambda x: x.related_person_id
            ),
            *column_task_revincludes(
                ("owner",), "owner", "RelatedPerson", lambda x: x.related_person_id
            ),
            *column_task_revincludes(
                ("requester",),
                "requester",
                "RelatedPerson",
                lambda x: x.related_person_id,
            ),
            *reference_medication_dispense_revincludes(
                "performer", "RelatedPerson", lambda x: x.related_person_id
            ),
            *reference_medication_administration_revincludes(
                "performer", "RelatedPerson", lambda x: x.related_person_id
            ),
            *column_medication_statement_revincludes(
                ("source",), "source", "RelatedPerson", lambda x: x.related_person_id
            ),
            *column_questionnaire_response_revincludes(
                ("author",), "author", "RelatedPerson", lambda x: x.related_person_id
            ),
            *column_questionnaire_response_revincludes(
                ("source",), "source", "RelatedPerson", lambda x: x.related_person_id
            ),
            *reference_document_reference_revincludes(
                "author", "RelatedPerson", lambda x: x.related_person_id
            ),
            *performer_care_plan_revincludes(
                "RelatedPerson", lambda x: x.related_person_id
            ),
            *participant_care_team_revincludes(
                "RelatedPerson", lambda p: p.related_person_id
            ),
            *actor_schedule_revincludes("RelatedPerson", lambda r: r.related_person_id),
            *managing_entity_group_revincludes(
                "RelatedPerson", lambda r: r.related_person_id
            ),
            *column_medication_request_revincludes(
                ("requester",),
                "requester",
                "RelatedPerson",
                lambda r: r.related_person_id,
            ),
            *column_medication_request_revincludes(
                ("intended-performer",),
                "performer",
                "RelatedPerson",
                lambda r: r.related_person_id,
            ),
            *column_service_request_revincludes(
                ("requester",),
                "requester",
                "RelatedPerson",
                lambda r: r.related_person_id,
            ),
            *performer_service_request_revincludes(
                "RelatedPerson", lambda r: r.related_person_id
            ),
            *participant_revincludes(
                "RelatedPerson", lambda r: r.related_person_id, ("actor",)
            ),
            *reference_observation_revincludes(
                "performer", "RelatedPerson", lambda r: r.related_person_id
            ),
            *actor_response_revincludes(
                "RelatedPerson", lambda r: r.related_person_id, ("actor",)
            ),
            *participant_encounter_revincludes(
                "RelatedPerson", lambda r: r.related_person_id, ("participant",)
            ),
            *actor_allergy_revincludes("RelatedPerson", lambda r: r.related_person_id),
            *asserter_condition_revincludes(
                "RelatedPerson", lambda r: r.related_person_id
            ),
            *performer_procedure_revincludes(
                "RelatedPerson", lambda r: r.related_person_id
            ),
            IncludeTarget(
                "Patient",
                "link",
                "RelatedPerson",
                _revinclude_patients_linking(lambda r: r.related_person_id),
                reverse=True,
            ),
        ),
        default_sort=lambda: [R.related_person_id.desc()],
    )
