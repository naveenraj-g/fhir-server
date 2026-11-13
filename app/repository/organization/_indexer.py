"""
FHIR Organization document -> search index. The only write-side mapper.

Organization's whole resource is stored verbatim in
OrganizationModel.content; this module derives every *other* column and
child row from it — exactly the values the FHIR R4 Organization search
parameters filter on (https://www.hl7.org/fhir/R4/organization.html#search),
nothing more. See OrganizationModel's docstring for the parameter -> storage
table; the shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from app.core.phonetic import phonetic_key
from app.fhir.search import normalize
from app.models.organization import (
    OrganizationAddress,
    OrganizationEndpoint,
    OrganizationIdentifier,
    OrganizationType,
)
from app.repository._content_index import (
    endpoint_row,
    identifier_rows,
    norms,
    reference_columns,
    relative,
    strings,
    type_rows,
)
from app.schemas.enums import AddressUse

from ._shared import _parse_endpoint_ref, _parse_org_ref

# Relationship attributes the index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "types", "addresses", "endpoints")


def partof_reference(document: dict) -> str | None:
    return relative((document.get("partOf") or {}).get("reference"), "Organization")


def assigner_references(document: dict) -> list[str]:
    refs = []
    for identifier in document.get("identifier") or []:
        ref = relative((identifier.get("assigner") or {}).get("reference"), "Organization")
        if ref:
            refs.append(ref)
    return refs


def index_columns(document: dict) -> dict:
    """Search columns on the organization row itself."""
    aliases = strings(document.get("alias"))
    return {
        "active": document.get("active"),
        "name": document.get("name"),
        "name_norm": normalize(document.get("name")),
        "alias": aliases,
        "alias_norm": norms(aliases),
        "name_phonetic": phonetic_key(document.get("name")),
        **reference_columns("partof", document.get("partOf"), "Organization", _parse_org_ref),
    }


def _address_row(a: dict) -> OrganizationAddress:
    lines = strings(a.get("line"))
    return OrganizationAddress(
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
    """Child index rows, keyed by OrganizationModel relationship name."""
    return {
        "identifiers": [
            r for i in document.get("identifier") or [] for r in identifier_rows(OrganizationIdentifier, i)
        ],
        "types": [r for cc in document.get("type") or [] for r in type_rows(OrganizationType, cc)],
        "addresses": [_address_row(a) for a in document.get("address") or []],
        "endpoints": [
            r
            for e in document.get("endpoint") or []
            if (r := endpoint_row(OrganizationEndpoint, e, _parse_endpoint_ref))
        ],
    }
