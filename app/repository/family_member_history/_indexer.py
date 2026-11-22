"""
FHIR FamilyMemberHistory document -> search index. The only write-side mapper.

FamilyMemberHistory's whole resource is stored verbatim in
FamilyMemberHistoryModel.content; this module derives every *other* column and child row
from it — exactly the values the FHIR R4 FamilyMemberHistory search parameters filter on
(https://www.hl7.org/fhir/R4/familymemberhistory.html#search), nothing more. See
FamilyMemberHistoryModel's docstring for the parameter -> storage table; the shared
builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.family_member_history import (
    REFERENCE_TYPES,
    FamilyMemberHistoryIdentifier,
    FamilyMemberHistoryInstantiatesUri,
    FamilyMemberHistoryReference,
    FamilyMemberHistoryStatus,
    FamilyMemberHistoryToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    type_rows,
)

from ._shared import typed


def index_columns(document: dict) -> dict:
    """Search columns on the family_member_history row itself."""
    status = document.get("status")
    try:
        status = FamilyMemberHistoryStatus(status) if status else None
    except ValueError:
        status = None  # the validator rejects a bad code before we get here
    value = document.get("date")
    start, end = (
        period_bounds({"start": value, "end": value}) if value else (None, None)
    )
    patient = document.get("patient") or {}
    reference = patient.get("reference")
    identifier = patient.get("identifier") or {}
    parsed = typed(reference, ("Patient",))
    return {
        "status": status,
        "date_start": start,
        "date_end": end,
        "patient_reference": reference,
        "patient_type": parsed[0] if parsed else None,
        "patient_id": parsed[1] if parsed else None,
        "patient_identifier_system": identifier.get("system"),
        "patient_identifier_value": identifier.get("value"),
    }


def _concept_rows(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(FamilyMemberHistoryToken, param=param), concept)
        if concept
        else []
    )


def _token_rows(document: dict) -> list:
    rows = []
    for condition in document.get("condition") or []:
        rows += _concept_rows("code", (condition or {}).get("code"))
    rows += _concept_rows("relationship", document.get("relationship"))
    rows += _concept_rows("sex", document.get("sex"))
    return rows


def _canonical_rows(document: dict) -> list:
    """One row per instantiatesCanonical URL (a list of strings, not References)."""
    rows = []
    for canonical in document.get("instantiatesCanonical") or []:
        if not canonical:
            continue
        parsed = typed(canonical, REFERENCE_TYPES["instantiates-canonical"])
        rows.append(
            FamilyMemberHistoryReference(
                param="instantiates-canonical",
                reference_reference=canonical,
                reference_type=parsed[0] if parsed else None,
                reference_id=parsed[1] if parsed else None,
            )
        )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by FamilyMemberHistoryModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(FamilyMemberHistoryIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _canonical_rows(document),
        "instantiates_uris": [
            FamilyMemberHistoryInstantiatesUri(uri=u)
            for u in document.get("instantiatesUri") or []
            if u
        ],
    }
