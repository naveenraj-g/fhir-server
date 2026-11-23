"""
FHIR MedicationDispense document -> search index. The only write-side mapper.

MedicationDispense's whole resource is stored verbatim in MedicationDispenseModel.content; this
module derives every *other* column and child row from it - exactly the values the FHIR R4
MedicationDispense search parameters filter on
(https://www.hl7.org/fhir/R4/medicationdispense.html#search), nothing more. See
MedicationDispenseModel's docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.medication_dispense import (
    CONTEXT_TYPES,
    DESTINATION_TYPES,
    MEDICATION_TYPES,
    REFERENCE_TYPES,
    SUBJECT_TYPES,
    MedicationDispenseIdentifier,
    MedicationDispenseReference,
    MedicationDispenseStatus,
    MedicationDispenseToken,
)
from app.repository._content_index import identifier_rows, period_bounds, type_rows

from ._shared import typed

_STATUSES = {m.value for m in MedicationDispenseStatus}


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


def _instant_range(value):
    """A 0..1 dateTime as the half-open range it covers at its written precision."""
    return period_bounds({"start": value, "end": value}) if value else (None, None)


def index_columns(document: dict) -> dict:
    """Search columns on the medication_dispense row itself."""
    status = document.get("status")
    prepared = _instant_range(document.get("whenPrepared"))
    handed = _instant_range(document.get("whenHandedOver"))
    return {
        "status": MedicationDispenseStatus(status) if status in _STATUSES else None,
        "whenprepared_start": prepared[0],
        "whenprepared_end": prepared[1],
        "whenhandedover_start": handed[0],
        "whenhandedover_end": handed[1],
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("context", document.get("context"), CONTEXT_TYPES),
        **_ref_columns(
            "medication", document.get("medicationReference"), MEDICATION_TYPES
        ),
        **_ref_columns("destination", document.get("destination"), DESTINATION_TYPES),
    }


def _token_rows(document: dict) -> list:
    rows = []
    medication = document.get("medicationCodeableConcept")
    if medication:
        rows += type_rows(partial(MedicationDispenseToken, param="code"), medication)
    dispense_type = document.get("type")
    if dispense_type:
        rows += type_rows(partial(MedicationDispenseToken, param="type"), dispense_type)
    return rows


def _reference_row(param: str, ref: dict | None):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = typed(reference, REFERENCE_TYPES[param])
    return MedicationDispenseReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = [
        _reference_row("performer", (p or {}).get("actor"))
        for p in document.get("performer") or []
    ]
    rows += [
        _reference_row("prescription", r)
        for r in document.get("authorizingPrescription") or []
    ]
    rows += [_reference_row("receiver", r) for r in document.get("receiver") or []]
    rows += [
        _reference_row("responsibleparty", r)
        for r in (document.get("substitution") or {}).get("responsibleParty") or []
    ]
    return [r for r in rows if r]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by MedicationDispenseModel relationship name."""
    return {
        "identifiers": [
            row
            for identifier in document.get("identifier") or []
            for row in identifier_rows(MedicationDispenseIdentifier, identifier)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
    }
