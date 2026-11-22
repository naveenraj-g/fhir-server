"""
FHIR Condition document -> search index. The only write-side mapper.

Condition's whole resource is stored verbatim in ConditionModel.content; this
module derives every *other* column and child row from it — exactly the values
the FHIR R4 Condition search parameters filter on
(https://www.hl7.org/fhir/R4/condition.html#search), nothing more. See
ConditionModel's docstring for the parameter -> storage table; the shared
builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from functools import partial

from app.fhir.search import normalize
from app.models.condition import (
    ACTOR_TYPES,
    SUBJECT_TYPES,
    ConditionEvidenceDetail,
    ConditionIdentifier,
    ConditionToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    type_rows,
)

from ._shared import any_typed, typed


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


def _instant_bounds(value):
    """(start, end) of the half-open range a dateTime covers at its written
    precision; (None, None) when absent."""
    return period_bounds({"start": value, "end": value}) if value else (None, None)


def _decimal(value) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:  # the validator rejects a non-number before we get here
        return None


def _quantity_bounds(age: dict | None, range_: dict | None) -> dict:
    """The (low, high, system, code, unit) of an Age (a point) or a Range, as the
    suffixes of one `{onset|abatement}_age_*` column group. A Range takes its unit
    from the low bound, or the high one when there is no low."""
    if age:
        value = _decimal(age.get("value"))
        return {
            "low": value,
            "high": value,
            "system": age.get("system"),
            "code": age.get("code"),
            "unit": age.get("unit"),
        }
    if range_:
        low, high = range_.get("low") or {}, range_.get("high") or {}
        unit = low if low.get("value") is not None else high
        return {
            "low": _decimal(low.get("value")),
            "high": _decimal(high.get("value")),
            "system": unit.get("system"),
            "code": unit.get("code"),
            "unit": unit.get("unit"),
        }
    return {"low": None, "high": None, "system": None, "code": None, "unit": None}


def _choice_columns(document: dict, element: str) -> dict:
    """The columns of onset[x] / abatement[x]: dateTime or Period as a range,
    Age or Range as quantity bounds, and the string."""
    if document.get(f"{element}DateTime"):
        start, end = _instant_bounds(document[f"{element}DateTime"])
    else:
        start, end = period_bounds(document.get(f"{element}Period"))
    quantity = _quantity_bounds(
        document.get(f"{element}Age"), document.get(f"{element}Range")
    )
    text = document.get(f"{element}String")
    return {
        f"{element}_date_start": start,
        f"{element}_date_end": end,
        f"{element}_age_low": quantity["low"],
        f"{element}_age_high": quantity["high"],
        f"{element}_age_system": quantity["system"],
        f"{element}_age_code": quantity["code"],
        f"{element}_age_unit": quantity["unit"],
        f"{element}_string": text,
        f"{element}_string_norm": normalize(text),
    }


def index_columns(document: dict) -> dict:
    """Search columns on the condition row itself."""
    recorded_start, recorded_end = _instant_bounds(document.get("recordedDate"))
    return {
        "recorded_date_start": recorded_start,
        "recorded_date_end": recorded_end,
        **_choice_columns(document, "onset"),
        **_choice_columns(document, "abatement"),
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ("Encounter",)),
        **_ref_columns("asserter", document.get("asserter"), ACTOR_TYPES),
    }


def _concept_rows(param: str, concept: dict | None) -> list:
    return type_rows(partial(ConditionToken, param=param), concept) if concept else []


def _token_rows(document: dict) -> list:
    rows = []
    rows += _concept_rows("clinical-status", document.get("clinicalStatus"))
    rows += _concept_rows("verification-status", document.get("verificationStatus"))
    rows += _concept_rows("severity", document.get("severity"))
    rows += _concept_rows("code", document.get("code"))
    for category in document.get("category") or []:
        rows += _concept_rows("category", category)
    for body_site in document.get("bodySite") or []:
        rows += _concept_rows("body-site", body_site)
    for stage in document.get("stage") or []:
        rows += _concept_rows("stage", stage.get("summary"))
    for evidence in document.get("evidence") or []:
        for code in evidence.get("code") or []:
            rows += _concept_rows("evidence", code)
    return rows


def _evidence_detail_rows(document: dict) -> list:
    rows = []
    for evidence in document.get("evidence") or []:
        for detail in evidence.get("detail") or []:
            reference = detail.get("reference")
            identifier = detail.get("identifier") or {}
            if not (reference or identifier.get("value")):
                continue
            parsed = any_typed(reference)
            rows.append(
                ConditionEvidenceDetail(
                    reference_reference=reference,
                    reference_type=parsed[0] if parsed else None,
                    reference_id=parsed[1] if parsed else None,
                    reference_identifier_system=identifier.get("system"),
                    reference_identifier_value=identifier.get("value"),
                )
            )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by ConditionModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(ConditionIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "evidence_details": _evidence_detail_rows(document),
    }
