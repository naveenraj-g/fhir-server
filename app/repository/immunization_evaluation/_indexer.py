"""
FHIR ImmunizationEvaluation document -> search index. The only write-side mapper.

ImmunizationEvaluation's whole resource is stored verbatim in
ImmunizationEvaluationModel.content; this module derives every *other* column and child
row from it — exactly the values the FHIR R4 ImmunizationEvaluation search parameters
filter on (https://www.hl7.org/fhir/R4/immunizationevaluation.html#search), nothing
more. See ImmunizationEvaluationModel's docstring for the parameter -> storage table; the
shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.immunization_evaluation import (
    ImmunizationEvaluationIdentifier,
    ImmunizationEvaluationStatus,
    ImmunizationEvaluationToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    type_rows,
)

from ._shared import typed


def _ref_columns(prefix: str, ref: dict | None, allowed: tuple[str, ...]) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the raw
    string), `{prefix}_type`/`{prefix}_id` (a relative `Type/<id>` of an
    allowed type) and `{prefix}_identifier_system`/`_value`."""
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
    """Search columns on the immunization_evaluation row itself."""
    status = document.get("status")
    try:
        status = ImmunizationEvaluationStatus(status) if status else None
    except ValueError:
        status = None  # the validator rejects a bad code before we get here
    value = document.get("date")
    start, end = (
        period_bounds({"start": value, "end": value}) if value else (None, None)
    )
    return {
        "status": status,
        "date_start": start,
        "date_end": end,
        **_ref_columns("patient", document.get("patient"), ("Patient",)),
        **_ref_columns(
            "immunization_event", document.get("immunizationEvent"), ("Immunization",)
        ),
    }


def _concept_rows(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(ImmunizationEvaluationToken, param=param), concept)
        if concept
        else []
    )


def _token_rows(document: dict) -> list:
    return _concept_rows("dose-status", document.get("doseStatus")) + _concept_rows(
        "target-disease", document.get("targetDisease")
    )


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by ImmunizationEvaluationModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(ImmunizationEvaluationIdentifier, i)
        ],
        "tokens": _token_rows(document),
    }
