"""
FHIR Location document -> search index. The only write-side mapper — same
arrangement as app.repository.organization._indexer.

Location's whole resource is stored verbatim in LocationModel.content; this
module derives every other column and child row from it — exactly the values
the FHIR R4 Location search parameters filter on
(https://www.hl7.org/fhir/R4/location.html#search). See LocationModel's
docstring for the parameter -> storage table.
"""

from __future__ import annotations

from decimal import Decimal

from app.fhir.search import normalize
from app.models.location import LocationEndpoint, LocationIdentifier, LocationStatus, LocationType
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

from ._shared import _parse_endpoint_ref, _parse_location_ref, _parse_org_ref

# Relationship attributes the index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "types", "endpoints")


def managing_organization_reference(document: dict) -> str | None:
    return relative((document.get("managingOrganization") or {}).get("reference"), "Organization")


def part_of_reference(document: dict) -> str | None:
    return relative((document.get("partOf") or {}).get("reference"), "Location")


def assigner_references(document: dict) -> list[str]:
    refs = []
    for identifier in document.get("identifier") or []:
        ref = relative((identifier.get("assigner") or {}).get("reference"), "Organization")
        if ref:
            refs.append(ref)
    return refs


def _decimal(value) -> Decimal | None:
    # str() first so a JSON float keeps its written digits rather than its
    # binary approximation.
    return None if value is None else Decimal(str(value))


def index_columns(document: dict) -> dict:
    """Search columns on the location row itself."""
    aliases = strings(document.get("alias"))
    status = document.get("status")
    op = document.get("operationalStatus") or {}
    address = document.get("address") or {}
    lines = strings(address.get("line"))
    position = document.get("position") or {}
    return {
        "status": LocationStatus(status) if status else None,
        "operational_status_system": op.get("system"),
        "operational_status_code": op.get("code"),
        "operational_status_display_norm": normalize(op.get("display")),
        "name": document.get("name"),
        "name_norm": normalize(document.get("name")),
        "alias": aliases,
        "alias_norm": norms(aliases),
        "address_use": AddressUse(address["use"]) if address.get("use") else None,
        "address_text": address.get("text"),
        "address_text_norm": normalize(address.get("text")),
        "address_line": lines,
        "address_line_norm": norms(lines),
        "address_city": address.get("city"),
        "address_city_norm": normalize(address.get("city")),
        "address_district": address.get("district"),
        "address_district_norm": normalize(address.get("district")),
        "address_state": address.get("state"),
        "address_state_norm": normalize(address.get("state")),
        "address_postal_code": address.get("postalCode"),
        "address_postal_code_norm": normalize(address.get("postalCode")),
        "address_country": address.get("country"),
        "address_country_norm": normalize(address.get("country")),
        **reference_columns(
            "managing_organization", document.get("managingOrganization"), "Organization", _parse_org_ref
        ),
        **reference_columns("part_of", document.get("partOf"), "Location", _parse_location_ref),
        "position_latitude": _decimal(position.get("latitude")),
        "position_longitude": _decimal(position.get("longitude")),
    }


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by LocationModel relationship name."""
    return {
        "identifiers": [
            r for i in document.get("identifier") or [] for r in identifier_rows(LocationIdentifier, i)
        ],
        "types": [r for cc in document.get("type") or [] for r in type_rows(LocationType, cc)],
        "endpoints": [
            r
            for e in document.get("endpoint") or []
            if (r := endpoint_row(LocationEndpoint, e, _parse_endpoint_ref))
        ],
    }
