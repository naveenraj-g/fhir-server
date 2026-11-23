"""
FHIR MedicationAdministration document -> search index. The only write-side mapper.

MedicationAdministration's whole resource is stored verbatim in
MedicationAdministrationModel.content; this module derives every *other* column and child row
from it - exactly the values the FHIR R4 MedicationAdministration search parameters filter on
(https://www.hl7.org/fhir/R4/medicationadministration.html#search), nothing more. See
MedicationAdministrationModel's docstring for the parameter -> storage table; the shared
builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.medication_administration import (
    CONTEXT_TYPES,
    MEDICATION_TYPES,
    REFERENCE_TYPES,
    REQUEST_TYPES,
    SUBJECT_TYPES,
    MedicationAdministrationIdentifier,
    MedicationAdministrationReference,
    MedicationAdministrationStatus,
    MedicationAdministrationToken,
)
from app.repository._content_index import identifier_rows, period_bounds, type_rows

from ._shared import typed

_STATUSES = {m.value for m in MedicationAdministrationStatus}


def _ref_columns(prefix: str, ref: dict | None, allowed: tuple[str, ...]) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the raw string),
    `{prefix}_type`/`{prefix}_id` (a relative `Type/<id>` of an allowed type) and
    `{prefix}_identifier_system`/`_value`."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    parsed = typed(reference, allowed)
    return {
        f"{prefix}_reference": reference,
        f"{prefix}_type": parsed[0] if parsed else None,
        f"{prefix}_id": parsed[1] if parsed else None,
        f"{prefix}_identifier_system": identifier.get("system"),
        f"{prefix}_identifier_value": identifier.get("value"),
    }


def _effective(document: dict):
    """effective[x] as the half-open range it covers: a dateTime is a point at its written
    precision, a Period runs from its start to the instant after its end."""
    value = document.get("effectiveDateTime")
    if value:
        return period_bounds({"start": value, "end": value})
    return period_bounds(document.get("effectivePeriod"))


def index_columns(document: dict) -> dict:
    """Search columns on the medication_administration row itself."""
    status = document.get("status")
    start, end = _effective(document)
    return {
        "status": MedicationAdministrationStatus(status)
        if status in _STATUSES
        else None,
        "effective_start": start,
        "effective_end": end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("context", document.get("context"), CONTEXT_TYPES),
        **_ref_columns(
            "medication", document.get("medicationReference"), MEDICATION_TYPES
        ),
        **_ref_columns("request", document.get("request"), REQUEST_TYPES),
    }


def _token_rows(document: dict) -> list:
    rows = []
    medication = document.get("medicationCodeableConcept")
    if medication:
        rows += type_rows(
            partial(MedicationAdministrationToken, param="code"), medication
        )
    for concept in document.get("reasonCode") or []:
        rows += type_rows(
            partial(MedicationAdministrationToken, param="reason-given"), concept
        )
    for concept in document.get("statusReason") or []:
        rows += type_rows(
            partial(MedicationAdministrationToken, param="reason-not-given"), concept
        )
    return rows


def _reference_row(param: str, ref: dict | None):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = typed(reference, REFERENCE_TYPES[param])
    return MedicationAdministrationReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = [_reference_row("device", r) for r in document.get("device") or []]
    rows += [
        _reference_row("performer", (p or {}).get("actor"))
        for p in document.get("performer") or []
    ]
    return [r for r in rows if r]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by MedicationAdministrationModel relationship name."""
    return {
        "identifiers": [
            row
            for identifier in document.get("identifier") or []
            for row in identifier_rows(MedicationAdministrationIdentifier, identifier)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
    }
