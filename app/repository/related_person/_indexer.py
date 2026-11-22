"""
FHIR RelatedPerson document -> search index. The only write-side mapper.

RelatedPerson's whole resource is stored verbatim in RelatedPersonModel.content;
this module derives every *other* column and child row from it — exactly the
values the FHIR R4 RelatedPerson search parameters filter on
(https://www.hl7.org/fhir/R4/relatedperson.html#search), nothing more. See
RelatedPersonModel's docstring for the parameter -> storage table; the shared
builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from app.core.phonetic import phonetic_key
from app.fhir.search import normalize
from app.models.related_person import (
    RelatedPersonAddress,
    RelatedPersonIdentifier,
    RelatedPersonName,
    RelatedPersonRelationship,
    RelatedPersonTelecom,
)
from app.repository._content_index import (
    identifier_rows,
    norms,
    period_bounds,
    strings,
    type_rows,
)
from app.schemas.enums import AddressUse, AdministrativeGender

from ._shared import typed


def index_columns(document: dict) -> dict:
    """Search columns on the related-person row itself."""
    gender = document.get("gender")
    try:
        gender = AdministrativeGender(gender) if gender else None
    except ValueError:
        gender = None  # the validator rejects a bad code before we get here
    birth = document.get("birthDate")
    birth_start, birth_end = period_bounds({"start": birth, "end": birth})
    patient = document.get("patient") or {}
    reference = patient.get("reference")
    identifier = patient.get("identifier") or {}
    parsed = typed(reference, ("Patient",))
    return {
        "active": document.get("active"),
        "gender": gender,
        "birth_date_start": birth_start,
        "birth_date_end": birth_end,
        "patient_reference": reference,
        "patient_type": parsed[0] if parsed else None,
        "patient_id": parsed[1] if parsed else None,
        "patient_identifier_system": identifier.get("system"),
        "patient_identifier_value": identifier.get("value"),
    }


def _name_row(n: dict) -> RelatedPersonName:
    given, prefix, suffix = (
        strings(n.get("given")),
        strings(n.get("prefix")),
        strings(n.get("suffix")),
    )
    phonetic_source = " ".join([n.get("family") or "", *(given or [])]).strip()
    return RelatedPersonName(
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


def _telecom_row(t: dict) -> RelatedPersonTelecom | None:
    if not t.get("value"):
        return None
    return RelatedPersonTelecom(
        system=t.get("system"), value=t["value"], use=t.get("use")
    )


def _address_row(a: dict) -> RelatedPersonAddress:
    lines = strings(a.get("line"))
    return RelatedPersonAddress(
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


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by RelatedPersonModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(RelatedPersonIdentifier, i)
        ],
        "names": [_name_row(n) for n in document.get("name") or []],
        "telecoms": [
            r for t in document.get("telecom") or [] if (r := _telecom_row(t))
        ],
        "addresses": [_address_row(a) for a in document.get("address") or []],
        "relationships": [
            r
            for concept in document.get("relationship") or []
            for r in type_rows(RelatedPersonRelationship, concept)
        ],
    }
