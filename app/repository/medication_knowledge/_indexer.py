"""
FHIR MedicationKnowledge document -> search index. The only write-side mapper.

MedicationKnowledge's whole resource is stored verbatim in MedicationKnowledgeModel.content;
this module derives every *other* column and child row from it - exactly the values the FHIR
R4 MedicationKnowledge search parameters filter on
(https://www.hl7.org/fhir/R4/medicationknowledge.html#search), nothing more. See
MedicationKnowledgeModel's docstring for the parameter -> storage table; the shared builders
are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create
and patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.medication_knowledge import (
    MANUFACTURER_TYPES,
    MedicationKnowledgeReference,
    MedicationKnowledgeStatus,
    MedicationKnowledgeToken,
)
from app.repository._content_index import type_rows

from ._shared import ref_type_and_id, typed

_STATUSES = {m.value for m in MedicationKnowledgeStatus}


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
    """Search columns on the medication_knowledge row itself."""
    status = document.get("status")
    return {
        "status": MedicationKnowledgeStatus(status) if status in _STATUSES else None,
        **_ref_columns(
            "manufacturer", document.get("manufacturer"), MANUFACTURER_TYPES
        ),
    }


def _concept(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(MedicationKnowledgeToken, param=param), concept)
        if isinstance(concept, dict)
        else []
    )


def _string(param: str, value) -> list:
    """A token search over a plain string: the string is the code, there is no system."""
    if isinstance(value, str) and value:
        return [MedicationKnowledgeToken(param=param, code=value)]
    return []


def _token_rows(document: dict) -> list:
    rows = _concept("code", document.get("code"))
    rows += _concept("doseform", document.get("doseForm"))
    for ingredient in document.get("ingredient") or []:
        rows += _concept(
            "ingredient-code", (ingredient or {}).get("itemCodeableConcept")
        )
    for classification in document.get("medicineClassification") or []:
        classification = classification or {}
        rows += _concept("classification-type", classification.get("type"))
        for concept in classification.get("classification") or []:
            rows += _concept("classification", concept)
    for monograph in document.get("monograph") or []:
        rows += _concept("monograph-type", (monograph or {}).get("type"))
    for program in document.get("monitoringProgram") or []:
        program = program or {}
        rows += _concept("monitoring-program-type", program.get("type"))
        rows += _string("monitoring-program-name", program.get("name"))
    for cost in document.get("cost") or []:
        rows += _string("source-cost", (cost or {}).get("source"))
    return rows


def _reference_row(param: str, ref: dict | None):
    """One index row for a Reference that has a `reference` or an `identifier`
    (display-only cannot be matched by a reference search)."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = ref_type_and_id(reference, param)
    return MedicationKnowledgeReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = [
        _reference_row("ingredient", (i or {}).get("itemReference"))
        for i in document.get("ingredient") or []
    ]
    rows += [
        _reference_row("monograph", (m or {}).get("source"))
        for m in document.get("monograph") or []
    ]
    return [r for r in rows if r is not None]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by MedicationKnowledgeModel relationship name."""
    return {
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
    }
