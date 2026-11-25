"""
FHIR PractitionerRole document -> search index. The only write-side mapper.

PractitionerRole's whole resource is stored verbatim in
PractitionerRoleModel.content; this module derives every *other* column and
child row from it — exactly the values the FHIR R4 PractitionerRole search
parameters filter on
(https://www.hl7.org/fhir/R4/practitionerrole.html#search), nothing more. See
PractitionerRoleModel's docstring for the parameter -> storage table; the
shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.practitioner_role import (
    REFERENCE_PARAMS,
    TOKEN_PARAMS,
    PractitionerRoleIdentifier,
    PractitionerRoleReference,
    PractitionerRoleTelecom,
    PractitionerRoleToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    reference_columns,
    relative,
    type_rows,
)

# Relationship attributes the index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "telecoms", "tokens", "references")


def index_columns(document: dict) -> dict:
    """Search columns on the practitioner_role row itself."""
    period_start, period_end = period_bounds(document.get("period"))
    return {
        "active": document.get("active"),
        "period_start": period_start,
        "period_end": period_end,
        **reference_columns(
            "practitioner", document.get("practitioner"), "Practitioner"
        ),
        **reference_columns(
            "organization", document.get("organization"), "Organization"
        ),
    }


def _telecom_row(t: dict) -> PractitionerRoleTelecom | None:
    if not t.get("value"):
        return None
    return PractitionerRoleTelecom(
        system=t.get("system"), value=t["value"], use=t.get("use")
    )


def _reference_row(
    param: str, resource_type: str, ref: dict
) -> PractitionerRoleReference | None:
    """One index row for a Reference with a `reference` or an `identifier`
    (display-only can't be matched by a reference search)."""
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    local = relative(reference, resource_type)
    tail = local.split("/", 1)[1] if local else ""
    ref_id = int(tail) if tail.isdigit() else None
    return PractitionerRoleReference(
        param=param,
        reference_reference=reference,
        reference_type=resource_type if ref_id is not None else None,
        reference_id=ref_id,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by PractitionerRoleModel relationship name."""
    tokens = []
    for param, element in TOKEN_PARAMS.items():
        model = partial(PractitionerRoleToken, param=param)
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
            for r in identifier_rows(PractitionerRoleIdentifier, i)
        ],
        "telecoms": [
            r for t in document.get("telecom") or [] if (r := _telecom_row(t))
        ],
        "tokens": tokens,
        "references": references,
    }
