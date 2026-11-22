"""
FHIR Medication document -> search index. The only write-side mapper.

Medication's whole resource is stored verbatim in MedicationModel.content; this module
derives every *other* column and child row from it — exactly the values the FHIR R4 Medication
search parameters filter on (https://www.hl7.org/fhir/R4/medication.html#search), nothing
more. See MedicationModel's docstring for the parameter -> storage table; the shared builders
are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create
and patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.medication import (
    MANUFACTURER_TYPES,
    MedicationIdentifier,
    MedicationReference,
    MedicationStatus,
    MedicationToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    relative,
    type_rows,
)

from ._shared import ref_type_and_id, typed

_STATUSES = {m.value for m in MedicationStatus}


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local reference that must
    exist in the caller's org on write: `identifier.assigner`, `manufacturer` (an
    Organization) and every `ingredient.itemReference` that is a Medication. Absolute URLs,
    logical (identifier-only) references and targets that are not resources on this server (a
    Substance ingredient) point elsewhere and are not checked."""
    refs = []

    def add(label, reference, resource_type):
        local = relative(reference, resource_type)
        if local:
            refs.append((label, resource_type, local))

    for identifier in document.get("identifier") or []:
        add(
            "identifier.assigner",
            (identifier.get("assigner") or {}).get("reference"),
            "Organization",
        )
    add(
        "manufacturer",
        (document.get("manufacturer") or {}).get("reference"),
        "Organization",
    )
    for ingredient in document.get("ingredient") or []:
        add(
            "ingredient.itemReference",
            ((ingredient or {}).get("itemReference") or {}).get("reference"),
            "Medication",
        )
    return refs


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


def index_columns(document: dict) -> dict:
    """Search columns on the medication row itself."""
    batch = document.get("batch") or {}
    expiration = batch.get("expirationDate")
    start, end = (
        period_bounds({"start": expiration, "end": expiration})
        if expiration
        else (None, None)
    )
    status = document.get("status")
    return {
        "status": MedicationStatus(status) if status in _STATUSES else None,
        "expiration_start": start,
        "expiration_end": end,
        "lot_number": batch.get("lotNumber"),
        **_ref_columns(
            "manufacturer", document.get("manufacturer"), MANUFACTURER_TYPES
        ),
    }


def _concept(param: str, concept: dict | None) -> list:
    return type_rows(partial(MedicationToken, param=param), concept) if concept else []


def _token_rows(document: dict) -> list:
    rows = _concept("code", document.get("code"))
    rows += _concept("form", document.get("form"))
    for ingredient in document.get("ingredient") or []:
        rows += _concept(
            "ingredient-code", (ingredient or {}).get("itemCodeableConcept")
        )
    return rows


def _reference_rows(document: dict) -> list:
    """One index row per ingredient.itemReference that has a `reference` or an `identifier`
    (display-only cannot be matched by a reference search)."""
    rows = []
    for ingredient in document.get("ingredient") or []:
        ref = (ingredient or {}).get("itemReference") or {}
        reference = ref.get("reference")
        identifier = ref.get("identifier") or {}
        if not (reference or identifier.get("value")):
            continue
        parsed = ref_type_and_id(reference, "ingredient")
        rows.append(
            MedicationReference(
                param="ingredient",
                reference_reference=reference,
                reference_type=parsed[0] if parsed else None,
                reference_id=parsed[1] if parsed else None,
                reference_identifier_system=identifier.get("system"),
                reference_identifier_value=identifier.get("value"),
            )
        )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by MedicationModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(MedicationIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
    }
