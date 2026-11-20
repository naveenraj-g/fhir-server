"""
FHIR R4 Practitioner search parameters
(https://www.hl7.org/fhir/R4/practitioner.html#search) plus the common
`_id` / `_lastUpdated`, declared once for app.fhir.search: parsing,
SQL, `_sort`, `_include`, and the OpenAPI docs all come from
practitioner_search() below. Same arrangement as
app.repository.organization.search.

Each parameter's SQL reads only the search index (PractitionerModel's
columns and child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.repository._appointment_revinclude import participant_revincludes
from app.repository._allergy_intolerance_revinclude import actor_allergy_revincludes
from app.repository._condition_revinclude import asserter_condition_revincludes
from app.repository._procedure_revinclude import performer_procedure_revincludes
from app.repository._diagnostic_report_revinclude import performer_report_revincludes
from app.repository._appointment_response_revinclude import actor_response_revincludes
from app.repository._encounter_revinclude import participant_encounter_revincludes
from app.fhir.search import IncludeTarget, MultiValueSort, SearchError, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    array_string_match,
    coded_token_match,
    date_match,
    string_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.models.practitioner import (
    PractitionerAddress,
    PractitionerCommunication,
    PractitionerIdentifier,
    PractitionerModel,
    PractitionerName,
    PractitionerTelecom,
)
from app.schemas.enums import AddressUse, AdministrativeGender

Prac = PractitionerModel
_ADDRESS_USE_SYSTEM = "http://hl7.org/fhir/address-use"
_GENDER_SYSTEM = "http://hl7.org/fhir/administrative-gender"


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(select(literal(1)).where(model.practitioner_pk == Prac.id, *conditions))


def _child_sort(column, model):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return select(fn(column)).where(model.practitioner_pk == Prac.id).scalar_subquery()

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(Prac.updated_at, Prac.created_at)


# ── _id ──────────────────────────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system or not (token.code or "").isdigit():  # ids are the numeric public id
        return false()
    return Prac.practitioner_id == int(token.code)


# ── active / gender / address-use (tokens with a fixed code system) ──────────


def _active_match(value, modifier, ctx):
    token = parse_token(value)
    if token.code not in ("true", "false") or token.system:  # boolean: no code system
        raise SearchError(value, f"'active' takes true or false, not '{value}'.")
    return Prac.active.is_(token.code == "true")


def _gender_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system is not None and token.system != _GENDER_SYSTEM:
        return false()  # another system, or `|code` (no system) — gender is always coded in its own
    if token.code is None:
        return Prac.gender.is_not(None)
    try:
        return Prac.gender == AdministrativeGender(token.code)
    except ValueError:
        return false()  # an unknown code matches nothing (not a failed enum cast)


def _address_use_match(value, modifier, ctx):
    token = parse_token(value)
    if token.system is not None and token.system != _ADDRESS_USE_SYSTEM:
        return false()
    if token.code is None:
        return _exists(PractitionerAddress, PractitionerAddress.use.is_not(None))
    try:
        use = AddressUse(token.code)
    except ValueError:
        return false()
    return _exists(PractitionerAddress, PractitionerAddress.use == use)


# ── names (HumanName) ────────────────────────────────────────────────────────

_N = PractitionerName


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

_A = PractitionerAddress
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
            *(string_match(raw, norm, value, modifier) for raw, norm in _ADDRESS_PARTS.values()),
        ),
    )


def _address_part(part):
    raw, norm = _ADDRESS_PARTS[part]

    def match(value, modifier, ctx):
        return _exists(_A, string_match(raw, norm, value, modifier))

    def present(ctx):
        return _exists(_A, raw.is_not(None))

    return match, present


# ── identifier / communication ───────────────────────────────────────────────

_I = PractitionerIdentifier
_C = PractitionerCommunication


def _identifier_match(value, modifier, ctx):
    if modifier == "text":
        return _exists(_I, token_text_match((_I.type_text_norm, _I.type_display_norm), value))
    if modifier == "of-type":
        type_system, type_code, ident = parse_of_type(value)
        return _exists(
            _I,
            _I.type_system == type_system,
            _I.type_code == type_code,
            _I.value == ident,
        )
    return _exists(_I, token_match(_I.system, _I.value, value))


def _communication_match(value, modifier, ctx):
    return _exists(
        _C,
        coded_token_match(_C.system, _C.code, value, modifier, (_C.text_norm, _C.display_norm)),
    )


# ── telecom (ContactPoint) ───────────────────────────────────────────────────

_T = PractitionerTelecom


def _telecom_match(system: str | None):
    """R4 token search on a ContactPoint: `code` matches `value`, the
    optional `system|` part matches `use`. `phone`/`email` also require
    ContactPoint.system to be that kind."""

    def match(value, modifier, ctx):
        condition = token_condition(_T.use, _T.value, parse_token(value))
        return _exists(_T, condition, _T.system == system) if system else _exists(_T, condition)

    return match


def _telecom_present(system: str | None):
    def present(ctx):
        return _exists(_T, _T.system == system) if system else _exists(_T)

    return present


# ── resource kind ────────────────────────────────────────────────────────────


async def _revinclude_practitioner_role(session, ctx, practitioners):
    """_revinclude=PractitionerRole:practitioner — the roles these
    practitioners hold."""
    from app.models.practitioner_role import PractitionerRoleModel as PR

    ids = {p.practitioner_id for p in practitioners}
    stmt = select(PR).where(PR.tenant_id == ctx.tenant_id, PR.practitioner_id.in_(ids))
    return list((await session.execute(stmt)).scalars().all())


def _revinclude_schedules(resource_type: str, key):
    """_revinclude=Schedule:actor — schedules with an actor of this type
    pointing at one of these rows (matched on the public id `key(row)`)."""

    async def fetch(session, ctx, rows):
        from app.models.schedule import ScheduleActor as A
        from app.models.schedule import ScheduleModel as S

        ids = {key(r) for r in rows}
        pks = select(A.schedule_pk).where(A.reference_type == resource_type, A.reference_id.in_(ids))
        stmt = select(S).where(S.tenant_id == ctx.tenant_id, S.id.in_(pks))
        return list((await session.execute(stmt)).scalars().all())

    return fetch


def _revinclude_patients(param: str, resource_type: str, key):
    """_revinclude=Patient:<param> — patients pointing at one of these rows
    (resolved lazily so the registries don't import each other at load)."""

    async def fetch(session, ctx, rows):
        from app.repository.patient.search import revinclude_patients_via_reference

        return await revinclude_patients_via_reference(param, resource_type, key)(session, ctx, rows)

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Practitioner rows."""
    from app.fhir.mappers.practitioner import to_fhir_practitioner
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "Practitioner",
            lambda p: p.practitioner_id,
            to_fhir_practitioner,
            "practitioners",
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
def practitioner_search() -> SearchRegistry:
    _register_kind()
    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public practitioner id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: Prac.practitioner_id,
            example="30001",
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
            "Whether the practitioner record is in active use",
            "Practitioner.active",
            _active_match,
            lambda ctx: Prac.active.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: Prac.active,
            example="true",
            modifier_docs={"not": "`:not` — active is not this value, or is not recorded at all."},
        ),
        SearchParam(
            "address",
            "string",
            "A server defined search that may match any of the string fields in the Address, including line, "
            "city, district, state, country, postalCode, and/or text",
            "Practitioner.address",
            _address_match,
            lambda ctx: _exists(_A),
            _STRING,
            example="Main St",
        ),
        SearchParam(
            "address-city",
            "string",
            "A city specified in an address",
            "Practitioner.address.city",
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
            "Practitioner.address.country",
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
            "Practitioner.address.postalCode",
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
            "Practitioner.address.state",
            _state,
            _state_present,
            _STRING,
            sort=lambda: _child_sort(_A.state_norm, _A),
            example="MA",
        ),
        SearchParam(
            "address-use",
            "token",
            "A use code specified in an address (home | work | temp | old | billing; system "
            f"{_ADDRESS_USE_SYSTEM})",
            "Practitioner.address.use",
            _address_use_match,
            lambda ctx: _exists(_A, _A.use.is_not(None)),
            frozenset({"not", "missing"}),
            example="work",
        ),
        SearchParam(
            "communication",
            "token",
            "One of the languages that the practitioner can communicate with",
            "Practitioner.communication",
            _communication_match,
            lambda ctx: _exists(_C),
            frozenset({"text", "not", "in", "not-in", "above", "below", "missing"}),
            sort=lambda: _child_sort(_C.code, _C),
            example="urn:ietf:bcp:47|en",
        ),
        SearchParam(
            "email",
            "token",
            "A value in an email contact (ContactPoint.value where system = email)",
            "Practitioner.telecom.where(system='email')",
            _telecom_match("email"),
            _telecom_present("email"),
            _TELECOM,
            example="adam@example.org",
        ),
        SearchParam(
            "family",
            "string",
            "A portion of the family name of the practitioner",
            "Practitioner.name.family",
            _family_match,
            lambda ctx: _exists(_N, _N.family.is_not(None)),
            _STRING,
            sort=lambda: _child_sort(_N.family_norm, _N),
            example="Careful",
        ),
        SearchParam(
            "gender",
            "token",
            f"Gender of the practitioner (male | female | other | unknown; system {_GENDER_SYSTEM})",
            "Practitioner.gender",
            _gender_match,
            lambda ctx: Prac.gender.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: Prac.gender,
            example="female",
        ),
        SearchParam(
            "given",
            "string",
            "A portion of the given name of the practitioner",
            "Practitioner.name.given",
            _given_match,
            lambda ctx: _exists(_N, _N.given.is_not(None)),
            _STRING,
            example="Adam",
        ),
        SearchParam(
            "identifier",
            "token",
            "A practitioner's Identifier",
            "Practitioner.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="http://hl7.org/fhir/sid/us-npi|9941339108",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "name",
            "string",
            "A server defined search that may match any of the string fields in the HumanName, including "
            "family, given, prefix, suffix, and/or text",
            "Practitioner.name",
            _name_match,
            lambda ctx: _exists(_N),
            _STRING,
            example="Careful",
        ),
        SearchParam(
            "phone",
            "token",
            "A value in a phone contact (ContactPoint.value where system = phone)",
            "Practitioner.telecom.where(system='phone')",
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
            "Practitioner.name",
            _phonetic_match,
            lambda ctx: _exists(_N, _N.phonetic.is_not(None)),
            example="Karefull",
        ),
        SearchParam(
            "telecom",
            "token",
            "The value in any kind of contact (ContactPoint.value; `use|value` also matches the use)",
            "Practitioner.telecom",
            _telecom_match(None),
            _telecom_present(None),
            _TELECOM,
            example="555-9988",
        ),
    ]

    return SearchRegistry(
        resource_type="Practitioner",
        params={p.name: p for p in params},
        summary_elements=frozenset({"identifier", "active", "name", "telecom", "address", "gender", "birthDate"}),
        # Practitioner has no Reference elements of its own to _include, and
        # the resources that point at a Practitioner (PractitionerRole,
        # Encounter, ...) aren't on this engine yet, so there is nothing to
        # _revinclude either.
        includes=(),
        # PractitionerRole.practitioner points here.
        revincludes=(
            *participant_revincludes('Practitioner', lambda p: p.practitioner_id, ('actor', 'practitioner')),
            *actor_response_revincludes('Practitioner', lambda p: p.practitioner_id, ('actor', 'practitioner')),
            *participant_encounter_revincludes('Practitioner', lambda p: p.practitioner_id, ('participant', 'practitioner')),
            *actor_allergy_revincludes('Practitioner', lambda p: p.practitioner_id),
            *asserter_condition_revincludes('Practitioner', lambda p: p.practitioner_id),
            *performer_procedure_revincludes('Practitioner', lambda p: p.practitioner_id),
            *performer_report_revincludes('Practitioner', lambda p: p.practitioner_id),
            IncludeTarget(
                "PractitionerRole", "practitioner", "Practitioner", _revinclude_practitioner_role, reverse=True
            ),
            # Schedule.actor points here.
            IncludeTarget(
                "Schedule", "actor", "Practitioner",
                _revinclude_schedules("Practitioner", lambda p: p.practitioner_id), reverse=True,
            ),
            # Patient.generalPractitioner points here.
            IncludeTarget(
                "Patient", "general-practitioner", "Practitioner",
                _revinclude_patients("general-practitioner", "Practitioner", lambda p: p.practitioner_id),
                reverse=True,
            ),
        ),
        default_sort=lambda: [Prac.practitioner_id.desc()],
    )
