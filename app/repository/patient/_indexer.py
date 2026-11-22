"""
FHIR Patient document -> search index. The only write-side mapper.

Patient's whole resource is stored verbatim in PatientModel.content; this
module derives every *other* column and child row from it — exactly the values
the FHIR R4 Patient search parameters filter on
(https://www.hl7.org/fhir/R4/patient.html#search), nothing more. See
PatientModel's docstring for the parameter -> storage table; the shared
builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from app.core.phonetic import phonetic_key
from app.fhir.search import normalize
from app.models.patient import (
    PatientAddress,
    PatientCommunication,
    PatientIdentifier,
    PatientName,
    PatientReference,
    PatientTelecom,
)
from app.repository._content_index import (
    identifier_rows,
    norms,
    period_bounds,
    reference_columns,
    strings,
    type_rows,
)
from app.schemas.enums import AddressUse, AdministrativeGender

from ._shared import ref_type_and_id

# Relationship attributes the index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = (
    "identifiers",
    "names",
    "telecoms",
    "addresses",
    "communications",
    "references",
)


def _deceased(document: dict) -> bool | None:
    """R4 `deceased`: Patient.deceased.exists() and Patient.deceased != false —
    True when deceasedDateTime is present or deceasedBoolean is true, False for
    deceasedBoolean false, None when neither is given."""
    if document.get("deceasedDateTime"):
        return True
    flag = document.get("deceasedBoolean")
    return flag if isinstance(flag, bool) else None


def index_columns(document: dict) -> dict:
    """Search columns on the patient row itself (not `user_id`, which is not
    part of the FHIR resource — it is set by the link call)."""
    gender = document.get("gender")
    try:
        gender = AdministrativeGender(gender) if gender else None
    except ValueError:
        gender = None  # the validator rejects a bad code before we get here
    birth = document.get("birthDate")
    death = document.get("deceasedDateTime")
    birth_start, birth_end = period_bounds({"start": birth, "end": birth})
    death_start, death_end = period_bounds({"start": death, "end": death})
    return {
        "active": document.get("active"),
        "gender": gender,
        "birth_date_start": birth_start,
        "birth_date_end": birth_end,
        "death_date_start": death_start,
        "death_date_end": death_end,
        "deceased": _deceased(document),
        **reference_columns(
            "managing_organization",
            document.get("managingOrganization"),
            "Organization",
        ),
    }


def _name_row(n: dict) -> PatientName:
    given, prefix, suffix = (
        strings(n.get("given")),
        strings(n.get("prefix")),
        strings(n.get("suffix")),
    )
    phonetic_source = " ".join([n.get("family") or "", *(given or [])]).strip()
    return PatientName(
        text=n.get("text"),
        text_norm=normalize(n.get("text")),
        family=n.get("family"),
        family_norm=normalize(n.get("family")),
        given=given,
        given_norm=norms(given),
        prefix=prefix,
        prefix_norm=norms(prefix),
        suffix=suffix,
        suffix_norm=norms(suffix),
        phonetic=phonetic_key(phonetic_source),
    )


def _telecom_row(t: dict) -> PatientTelecom | None:
    if not t.get("value"):
        return None
    return PatientTelecom(system=t.get("system"), value=t["value"], use=t.get("use"))


def _address_row(a: dict) -> PatientAddress:
    lines = strings(a.get("line"))
    return PatientAddress(
        use=AddressUse(a["use"]) if a.get("use") else None,
        text=a.get("text"),
        text_norm=normalize(a.get("text")),
        line=lines,
        line_norm=norms(lines),
        city=a.get("city"),
        city_norm=normalize(a.get("city")),
        district=a.get("district"),
        district_norm=normalize(a.get("district")),
        state=a.get("state"),
        state_norm=normalize(a.get("state")),
        postal_code=a.get("postalCode"),
        postal_code_norm=normalize(a.get("postalCode")),
        country=a.get("country"),
        country_norm=normalize(a.get("country")),
    )


def _reference_row(param: str, ref: dict | None) -> PatientReference | None:
    """One index row for a Reference with a `reference` or an `identifier`
    (display-only can't be matched by a reference search)."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = ref_type_and_id(reference, param)
    return PatientReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by PatientModel relationship name."""
    references = [
        r
        for gp in document.get("generalPractitioner") or []
        if (r := _reference_row("general-practitioner", gp))
    ]
    references += [
        r
        for link in document.get("link") or []
        if (r := _reference_row("link", link.get("other")))
    ]
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(PatientIdentifier, i)
        ],
        "names": [_name_row(n) for n in document.get("name") or []],
        "telecoms": [
            r for t in document.get("telecom") or [] if (r := _telecom_row(t))
        ],
        "addresses": [_address_row(a) for a in document.get("address") or []],
        "communications": [
            r
            for c in document.get("communication") or []
            if c.get("language")
            for r in type_rows(PatientCommunication, c["language"])
        ],
        "references": references,
    }
