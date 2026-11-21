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
from app.repository._content_index import identifier_rows, period_bounds, relative, type_rows

from ._shared import typed

# Of the six `reasonReference` targets, these are resources here (Observation,
# QuestionnaireResponse and DocumentReference are not rebuilt yet).
_MODELED_REASONS = ("Condition", "AllergyIntolerance", "DiagnosticReport")
_AUTHOR_TYPES = ("Practitioner", "PractitionerRole", "Patient", "RelatedPerson", "Organization")


def _notes(document: dict) -> list[dict]:
    """Every note: the resource's own and each condition's."""
    notes = list(document.get("note") or [])
    for condition in document.get("condition") or []:
        notes += (condition or {}).get("note") or []
    return notes


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local
    reference that must exist in the caller's org on write: identifier.assigner,
    `patient`, `reasonReference` that is a Condition, AllergyIntolerance or DiagnosticReport,
    and every note's `authorReference`. Absolute URLs, logical (identifier-only) references
    and targets that are not resources on this server (an Observation reason) point
    elsewhere and are not checked."""
    refs = []

    def add(label, reference, resource_type):
        local = relative(reference, resource_type)
        if local:
            refs.append((label, resource_type, local))

    for identifier in document.get("identifier") or []:
        add("identifier.assigner", (identifier.get("assigner") or {}).get("reference"), "Organization")
    add("patient", (document.get("patient") or {}).get("reference"), "Patient")
    for ref in document.get("reasonReference") or []:
        parsed = typed((ref or {}).get("reference"), _MODELED_REASONS)
        if parsed:
            refs.append(("reasonReference", parsed[0], ref["reference"]))
    for note in _notes(document):
        parsed = typed(((note or {}).get("authorReference") or {}).get("reference"), _AUTHOR_TYPES)
        if parsed:
            refs.append(("note.authorReference", parsed[0], note["authorReference"]["reference"]))
    return refs


def index_columns(document: dict) -> dict:
    """Search columns on the family_member_history row itself."""
    status = document.get("status")
    try:
        status = FamilyMemberHistoryStatus(status) if status else None
    except ValueError:
        status = None  # the validator rejects a bad code before we get here
    value = document.get("date")
    start, end = period_bounds({"start": value, "end": value}) if value else (None, None)
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
    return type_rows(partial(FamilyMemberHistoryToken, param=param), concept) if concept else []


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
            r for i in document.get("identifier") or [] for r in identifier_rows(FamilyMemberHistoryIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _canonical_rows(document),
        "instantiates_uris": [
            FamilyMemberHistoryInstantiatesUri(uri=u) for u in document.get("instantiatesUri") or [] if u
        ],
    }
