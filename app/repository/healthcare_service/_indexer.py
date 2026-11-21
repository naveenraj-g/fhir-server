"""
FHIR HealthcareService document -> search index. The only write-side mapper.

HealthcareService's whole resource is stored verbatim in
HealthcareServiceModel.content; this module derives every *other* column and
child row from it — exactly the values the FHIR R4 HealthcareService search
parameters filter on
(https://www.hl7.org/fhir/R4/healthcareservice.html#search), nothing more.
See HealthcareServiceModel's docstring for the parameter -> storage table;
the shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.fhir.search import normalize
from app.models.healthcare_service import (
    REFERENCE_PARAMS,
    TOKEN_PARAMS,
    HealthcareServiceIdentifier,
    HealthcareServiceReference,
    HealthcareServiceToken,
)
from app.repository._content_index import (
    identifier_rows,
    reference_columns,
    relative,
    type_rows,
)

from ._shared import _parse_org_ref

# Relationship attributes the index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "tokens", "references")


def organization_references(document: dict) -> list[tuple[str, str]]:
    """(element label, relative Organization reference) for every local
    Reference(Organization): providedBy and identifier.assigner."""
    refs = []
    provided_by = relative(
        (document.get("providedBy") or {}).get("reference"), "Organization"
    )
    if provided_by:
        refs.append(("providedBy", provided_by))
    for identifier in document.get("identifier") or []:
        ref = relative(
            (identifier.get("assigner") or {}).get("reference"), "Organization"
        )
        if ref:
            refs.append(("identifier.assigner", ref))
    return refs


def location_references(document: dict) -> list[tuple[str, str]]:
    """(element label, relative Location reference) for every local
    Reference(Location): location[] and coverageArea[]."""
    refs = []
    for element in ("location", "coverageArea"):
        for ref in document.get(element) or []:
            local = relative(ref.get("reference"), "Location")
            if local:
                refs.append((element, local))
    return refs


def endpoint_references(document: dict) -> list[str]:
    """Relative `Endpoint/<id>` references in `endpoint[]` — the only shape
    that can resolve to a local Endpoint (an absolute URL, or an endpoint
    given only by identifier/display, is stored as sent and not checked)."""
    refs = []
    for ref in document.get("endpoint") or []:
        local = relative(ref.get("reference"), "Endpoint")
        if local:
            refs.append(local)
    return refs


def index_columns(document: dict) -> dict:
    """Search columns on the healthcare_service row itself."""
    return {
        "active": document.get("active"),
        "name": document.get("name"),
        "name_norm": normalize(document.get("name")),
        **reference_columns(
            "provided_by", document.get("providedBy"), "Organization", _parse_org_ref
        ),
    }


def _reference_row(
    param: str, resource_type: str, ref: dict
) -> HealthcareServiceReference | None:
    """One index row for a Reference with a `reference` or an `identifier`
    (display-only can't be matched by a reference search)."""
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    local = relative(reference, resource_type)
    tail = local.split("/", 1)[1] if local else ""
    ref_id = int(tail) if tail.isdigit() else None
    return HealthcareServiceReference(
        param=param,
        reference_reference=reference,
        reference_type=resource_type if ref_id is not None else None,
        reference_id=ref_id,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by HealthcareServiceModel relationship name."""
    tokens = []
    for param, element in TOKEN_PARAMS.items():
        model = partial(HealthcareServiceToken, param=param)
        for concept in document.get(element) or []:
            tokens.extend(type_rows(model, concept))
    references = []
    for param, (element, resource_type) in REFERENCE_PARAMS.items():
        for ref in document.get(element) or []:
            if row := _reference_row(param, resource_type, ref):
                references.append(row)
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(HealthcareServiceIdentifier, i)
        ],
        "tokens": tokens,
        "references": references,
    }
