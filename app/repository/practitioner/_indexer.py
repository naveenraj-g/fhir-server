"""
FHIR Practitioner document -> search index. The only write-side mapper.

Practitioner's whole resource is stored verbatim in
PractitionerModel.content; this module derives every *other* column and
child row from it — exactly the values the FHIR R4 Practitioner search
parameters filter on (https://www.hl7.org/fhir/R4/practitioner.html#search),
nothing more. See PractitionerModel's docstring for the parameter -> storage
table; the shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from app.core.phonetic import phonetic_key
from app.fhir.mappers.content import EXT_BASE
from app.fhir.search import normalize
from app.models.practitioner import (
    PractitionerAddress,
    PractitionerCommunication,
    PractitionerIdentifier,
    PractitionerName,
    PractitionerTelecom,
)
from app.repository._content_index import (
    identifier_rows,
    norms,
    relative,
    strings,
    type_rows,
)
from app.schemas.enums import AddressUse, AdministrativeGender

# Relationship attributes the index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "names", "telecoms", "addresses", "communications")

# The one non-FHIR piece of state a Practitioner carries: which end-user owns
# the record (drives `/me`). Sent as this extension with a `valueString`.
USER_ID_EXTENSION_URL = f"{EXT_BASE}/user-id"


def user_id_of(document: dict) -> str | None:
    """The end-user id carried by the user-id extension, if any."""
    for ext in document.get("extension") or []:
        if ext.get("url") == USER_ID_EXTENSION_URL and ext.get("valueString"):
            return ext["valueString"]
    return None


def organization_references(document: dict) -> list[tuple[str, str]]:
    """(element label, relative Organization reference) for every local
    Reference(Organization) in the document — identifier.assigner and
    qualification.issuer — so each can be existence-checked on write."""
    refs = []
    for identifier in document.get("identifier") or []:
        ref = relative((identifier.get("assigner") or {}).get("reference"), "Organization")
        if ref:
            refs.append(("identifier.assigner", ref))
    for qualification in document.get("qualification") or []:
        ref = relative((qualification.get("issuer") or {}).get("reference"), "Organization")
        if ref:
            refs.append(("qualification.issuer", ref))
    return refs


def index_columns(document: dict) -> dict:
    """Search columns on the practitioner row itself (not `user_id`, which
    is set once at create)."""
    gender = document.get("gender")
    try:
        gender = AdministrativeGender(gender) if gender else None
    except ValueError:
        gender = None  # the validator rejects a bad code before we get here
    return {"active": document.get("active"), "gender": gender}


def _name_row(n: dict) -> PractitionerName:
    given, prefix, suffix = strings(n.get("given")), strings(n.get("prefix")), strings(n.get("suffix"))
    phonetic_source = " ".join([n.get("family") or "", *(given or [])]).strip()
    return PractitionerName(
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


def _telecom_row(t: dict) -> PractitionerTelecom | None:
    if not t.get("value"):
        return None
    return PractitionerTelecom(system=t.get("system"), value=t["value"], use=t.get("use"))


def _address_row(a: dict) -> PractitionerAddress:
    lines = strings(a.get("line"))
    return PractitionerAddress(
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
    """Child index rows, keyed by PractitionerModel relationship name."""
    return {
        "identifiers": [
            r for i in document.get("identifier") or [] for r in identifier_rows(PractitionerIdentifier, i)
        ],
        "names": [_name_row(n) for n in document.get("name") or []],
        "telecoms": [r for t in document.get("telecom") or [] if (r := _telecom_row(t))],
        "addresses": [_address_row(a) for a in document.get("address") or []],
        "communications": [
            r for cc in document.get("communication") or [] for r in type_rows(PractitionerCommunication, cc)
        ],
    }
