"""
FHIR Endpoint document -> search index. The only write-side mapper.

Endpoint's whole resource is stored verbatim in EndpointModel.content; this
module derives every *other* column and child row from it — exactly the
values the FHIR R4 Endpoint search parameters filter on
(https://www.hl7.org/fhir/R4/endpoint.html#search), nothing more. See
EndpointModel's docstring for the parameter -> storage table; the shared
builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from app.fhir.search import normalize
from app.models.endpoint import EndpointIdentifier, EndpointPayloadType, EndpointStatus
from app.repository._content_index import (
    identifier_rows,
    reference_columns,
    relative,
    type_rows,
)

from ._shared import _parse_org_ref

# Relationship attributes the index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "payload_types")


def organization_references(document: dict) -> list[tuple[str, str]]:
    """(element label, relative Organization reference) for every local
    Reference(Organization): managingOrganization and identifier.assigner."""
    refs = []
    managing = relative(
        (document.get("managingOrganization") or {}).get("reference"), "Organization"
    )
    if managing:
        refs.append(("managingOrganization", managing))
    for identifier in document.get("identifier") or []:
        ref = relative(
            (identifier.get("assigner") or {}).get("reference"), "Organization"
        )
        if ref:
            refs.append(("identifier.assigner", ref))
    return refs


def index_columns(document: dict) -> dict:
    """Search columns on the endpoint row itself."""
    status = document.get("status")
    try:
        status = EndpointStatus(status) if status else None
    except ValueError:
        status = None  # the validator rejects a bad code before we get here
    connection_type = document.get("connectionType") or {}
    return {
        "status": status,
        "connection_type_system": connection_type.get("system"),
        "connection_type_code": connection_type.get("code"),
        "connection_type_display_norm": normalize(connection_type.get("display")),
        "name": document.get("name"),
        "name_norm": normalize(document.get("name")),
        **reference_columns(
            "managing_organization",
            document.get("managingOrganization"),
            "Organization",
            _parse_org_ref,
        ),
    }


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by EndpointModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(EndpointIdentifier, i)
        ],
        "payload_types": [
            r
            for cc in document.get("payloadType") or []
            for r in type_rows(EndpointPayloadType, cc)
        ],
    }
