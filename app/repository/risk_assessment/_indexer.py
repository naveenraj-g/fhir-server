"""
FHIR RiskAssessment document -> search index. The only write-side mapper.

RiskAssessment's whole resource is stored verbatim in RiskAssessmentModel.content; this
module derives every *other* column and child row from it — exactly the values the FHIR R4
RiskAssessment search parameters filter on
(https://www.hl7.org/fhir/R4/riskassessment.html#search), nothing more. See
RiskAssessmentModel's docstring for the parameter -> storage table; the shared builders are
in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from functools import partial

from app.models.risk_assessment import (
    PERFORMER_TYPES,
    SUBJECT_TYPES,
    RiskAssessmentIdentifier,
    RiskAssessmentPrediction,
    RiskAssessmentToken,
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
    """Search columns on the risk_assessment row itself."""
    value = document.get("occurrenceDateTime")
    start, end = (
        period_bounds({"start": value, "end": value}) if value else (None, None)
    )
    return {
        "date_start": start,
        "date_end": end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ("Encounter",)),
        **_ref_columns("condition", document.get("condition"), ("Condition",)),
        **_ref_columns("performer", document.get("performer"), PERFORMER_TYPES),
    }


def _concept_rows(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(RiskAssessmentToken, param=param), concept) if concept else []
    )


def _token_rows(document: dict) -> list:
    rows = _concept_rows("method", document.get("method"))
    for prediction in document.get("prediction") or []:
        rows += _concept_rows("risk", (prediction or {}).get("qualitativeRisk"))
    return rows


def _number(value) -> Decimal | None:
    """A JSON number as a Decimal (None if absent or not a number — the validator rejects a bad
    value before we get here)."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _prediction_rows(document: dict) -> list:
    """One row per prediction that has a probability: a decimal is a point (low == high), a
    Range has its two bounds, either of which may be absent."""
    rows = []
    for prediction in document.get("prediction") or []:
        prediction = prediction or {}
        if prediction.get("probabilityDecimal") is not None:
            low = high = _number(prediction["probabilityDecimal"])
        else:
            probability = prediction.get("probabilityRange") or {}
            low = _number((probability.get("low") or {}).get("value"))
            high = _number((probability.get("high") or {}).get("value"))
        if low is not None or high is not None:
            rows.append(
                RiskAssessmentPrediction(probability_low=low, probability_high=high)
            )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by RiskAssessmentModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(RiskAssessmentIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "predictions": _prediction_rows(document),
    }
