"""Payload -> FHIR JSON conversion for RiskAssessment.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(RiskAssessmentCreateSchema / RiskAssessmentPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.schemas.risk_assessment.input import (
        RiskAssessmentCodeableConceptInput,
        RiskAssessmentCreateSchema,
        RiskAssessmentIdentifierInput,
        RiskAssessmentNoteInput,
        RiskAssessmentPatchSchema,
        RiskAssessmentPredictionInput,
    )


def _val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _format_datetime(val: Any) -> str | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=timezone.utc)
        return val.isoformat()
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


def _coding_from_payload(c: Any) -> dict:
    if isinstance(c, dict):
        return {
            k: v
            for k, v in {
                "system": c.get("system"),
                "version": c.get("version"),
                "code": c.get("code"),
                "display": c.get("display"),
                "userSelected": c.get("user_selected"),
            }.items()
            if v is not None
        }
    return {
        k: v
        for k, v in {
            "system": getattr(c, "system", None),
            "version": getattr(c, "version", None),
            "code": getattr(c, "code", None),
            "display": getattr(c, "display", None),
            "userSelected": getattr(c, "user_selected", None),
        }.items()
        if v is not None
    }


def payload_risk_assessment_codeable_concept(
    cc: RiskAssessmentCodeableConceptInput | dict | None,
) -> dict | None:
    if not cc:
        return None
    codings = _val(cc, "coding") or []
    text = _val(cc, "text")

    coding_list = [_coding_from_payload(c) for c in codings]
    coding_list = [c for c in coding_list if c]

    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _reference_with_identifier_from_payload(ref: Any) -> dict:
    if not ref:
        return {}

    if isinstance(ref, str):
        return {"reference": ref}

    raw_reference = _val(ref, "reference")
    display = _val(ref, "reference_display")

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    if display:
        entry["display"] = display

    id_use = _val(ref, "reference_identifier_use")
    id_type_system = _val(ref, "reference_identifier_type_system")
    id_type_version = _val(ref, "reference_identifier_type_version")
    id_type_code = _val(ref, "reference_identifier_type_code")
    id_type_display = _val(ref, "reference_identifier_type_display")
    id_type_user_selected = _val(ref, "reference_identifier_type_user_selected")
    id_type_text = _val(ref, "reference_identifier_type_text")
    id_system = _val(ref, "reference_identifier_system")
    id_value = _val(ref, "reference_identifier_value")
    id_period_start = _val(ref, "reference_identifier_period_start")
    id_period_end = _val(ref, "reference_identifier_period_end")

    if (
        id_use
        or id_type_system
        or id_type_version
        or id_type_code
        or id_type_display
        or id_type_user_selected
        or id_type_text
        or id_system
        or id_value
        or id_period_start
        or id_period_end
    ):
        identifier: dict = {}
        if id_use:
            identifier["use"] = getattr(id_use, "value", str(id_use))
        if (
            id_type_system
            or id_type_code
            or id_type_text
            or id_type_display
            or id_type_version
            or id_type_user_selected
        ):
            type_cc: dict = {}
            if id_type_system or id_type_code or id_type_display or id_type_version or id_type_user_selected:
                type_cc["coding"] = [
                    {
                        k: v
                        for k, v in {
                            "system": id_type_system,
                            "version": id_type_version,
                            "code": id_type_code,
                            "display": id_type_display,
                            "userSelected": id_type_user_selected,
                        }.items()
                        if v is not None
                    }
                ]
            if id_type_text:
                type_cc["text"] = id_type_text
            identifier["type"] = type_cc
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_period_start or id_period_end:
            identifier["period"] = {
                k: v
                for k, v in {
                    "start": _format_datetime(id_period_start) if id_period_start else None,
                    "end": _format_datetime(id_period_end) if id_period_end else None,
                }.items()
                if v is not None
            }
        entry["identifier"] = identifier

    return entry


def payload_risk_assessment_identifier(i: RiskAssessmentIdentifierInput | dict) -> dict:
    assigner_raw = _val(i, "assigner")
    assigner_display = _val(i, "assigner_display")
    assigner_entry: dict = {}
    if assigner_raw:
        assigner_entry["reference"] = assigner_raw
    if assigner_display:
        assigner_entry["display"] = assigner_display

    assigner_id_use = _val(i, "assigner_identifier_use")
    assigner_id_system = _val(i, "assigner_identifier_system")
    assigner_id_value = _val(i, "assigner_identifier_value")
    if assigner_id_use or assigner_id_system or assigner_id_value:
        assigner_identifier: dict = {}
        if assigner_id_use:
            assigner_identifier["use"] = getattr(assigner_id_use, "value", str(assigner_id_use))
        if assigner_id_system:
            assigner_identifier["system"] = assigner_id_system
        if assigner_id_value:
            assigner_identifier["value"] = assigner_id_value
        assigner_entry["identifier"] = assigner_identifier

    type_cc = payload_risk_assessment_codeable_concept(_val(i, "type"))

    period_start = _val(i, "period_start")
    period_end = _val(i, "period_end")
    period = None
    if period_start or period_end:
        period = {
            k: v
            for k, v in {
                "start": _format_datetime(period_start) if period_start else None,
                "end": _format_datetime(period_end) if period_end else None,
            }.items()
            if v is not None
        }

    use = _val(i, "use")

    return {
        k: v
        for k, v in {
            "use": getattr(use, "value", str(use)) if use else None,
            "type": type_cc,
            "system": _val(i, "system"),
            "value": _val(i, "value"),
            "period": period,
            "assigner": assigner_entry or None,
        }.items()
        if v is not None
    }


def payload_risk_assessment_note(n: RiskAssessmentNoteInput | dict) -> dict:
    text = _val(n, "text")
    time_val = _val(n, "time")
    author_str = _val(n, "author_string")
    author_ref_raw = _val(n, "author_reference")

    entry: dict[str, Any] = {"text": text}
    if time_val:
        entry["time"] = _format_datetime(time_val)
    if author_str:
        entry["authorString"] = author_str
    elif author_ref_raw:
        author_ref_entry = _reference_with_identifier_from_payload(
            {
                "reference": author_ref_raw,
                "reference_display": _val(n, "author_display"),
                "reference_identifier_use": _val(n, "author_identifier_use"),
                "reference_identifier_type_system": _val(n, "author_identifier_type_system"),
                "reference_identifier_type_version": _val(n, "author_identifier_type_version"),
                "reference_identifier_type_code": _val(n, "author_identifier_type_code"),
                "reference_identifier_type_display": _val(n, "author_identifier_type_display"),
                "reference_identifier_type_user_selected": _val(n, "author_identifier_type_user_selected"),
                "reference_identifier_type_text": _val(n, "author_identifier_type_text"),
                "reference_identifier_system": _val(n, "author_identifier_system"),
                "reference_identifier_value": _val(n, "author_identifier_value"),
                "reference_identifier_period_start": _val(n, "author_identifier_period_start"),
                "reference_identifier_period_end": _val(n, "author_identifier_period_end"),
            }
        )
        if author_ref_entry:
            entry["authorReference"] = author_ref_entry
    return entry


def payload_risk_assessment_prediction(p: RiskAssessmentPredictionInput | dict) -> dict:
    outcome = payload_risk_assessment_codeable_concept(_val(p, "outcome"))
    qualitative_risk = payload_risk_assessment_codeable_concept(_val(p, "qualitative_risk"))

    pred: dict[str, Any] = {}
    if outcome:
        pred["outcome"] = outcome

    prob_dec = _val(p, "probability_decimal")
    if prob_dec is not None:
        pred["probabilityDecimal"] = float(prob_dec)
    else:
        prob_range_in = _val(p, "probability_range")
        if prob_range_in:
            low = _val(prob_range_in, "low")
            high = _val(prob_range_in, "high")
            range_dict: dict[str, Any] = {}
            if low:
                range_dict["low"] = {
                    k: v
                    for k, v in {
                        "value": _val(low, "value"),
                        "unit": _val(low, "unit"),
                        "system": _val(low, "system"),
                        "code": _val(low, "code"),
                    }.items()
                    if v is not None
                }
            if high:
                range_dict["high"] = {
                    k: v
                    for k, v in {
                        "value": _val(high, "value"),
                        "unit": _val(high, "unit"),
                        "system": _val(high, "system"),
                        "code": _val(high, "code"),
                    }.items()
                    if v is not None
                }
            if range_dict:
                pred["probabilityRange"] = range_dict

    if qualitative_risk:
        pred["qualitativeRisk"] = qualitative_risk

    rel_risk = _val(p, "relative_risk")
    if rel_risk is not None:
        pred["relativeRisk"] = float(rel_risk)

    when_period_in = _val(p, "when_period")
    if when_period_in:
        pred["whenPeriod"] = {
            k: v
            for k, v in {
                "start": _format_datetime(_val(when_period_in, "start")),
                "end": _format_datetime(_val(when_period_in, "end")),
            }.items()
            if v is not None
        }
    else:
        when_range_in = _val(p, "when_range")
        if when_range_in:
            low = _val(when_range_in, "low")
            high = _val(when_range_in, "high")
            range_dict = {}
            if low:
                range_dict["low"] = {
                    k: v
                    for k, v in {
                        "value": _val(low, "value"),
                        "unit": _val(low, "unit"),
                        "system": _val(low, "system"),
                        "code": _val(low, "code"),
                    }.items()
                    if v is not None
                }
            if high:
                range_dict["high"] = {
                    k: v
                    for k, v in {
                        "value": _val(high, "value"),
                        "unit": _val(high, "unit"),
                        "system": _val(high, "system"),
                        "code": _val(high, "code"),
                    }.items()
                    if v is not None
                }
            if range_dict:
                pred["whenRange"] = range_dict

    rationale = _val(p, "rationale")
    if rationale:
        pred["rationale"] = rationale

    return pred


def payload_to_fhir_risk_assessment(payload: RiskAssessmentCreateSchema) -> dict[str, Any]:
    """Convert a RiskAssessmentCreateSchema payload directly to a FHIR R4 dict for pre-write validation."""
    status_val = getattr(payload.status, "value", str(payload.status))
    result: dict[str, Any] = {
        "resourceType": "RiskAssessment",
        "status": status_val,
    }

    if payload.subject:
        result["subject"] = _reference_with_identifier_from_payload(payload.subject)

    if payload.based_on:
        result["basedOn"] = _reference_with_identifier_from_payload(payload.based_on)

    if payload.parent:
        result["parent"] = _reference_with_identifier_from_payload(payload.parent)

    if payload.encounter:
        result["encounter"] = _reference_with_identifier_from_payload(payload.encounter)

    if payload.occurrence_date_time:
        result["occurrenceDateTime"] = _format_datetime(payload.occurrence_date_time)
    elif payload.occurrence_period_start or payload.occurrence_period_end:
        result["occurrencePeriod"] = {
            k: v
            for k, v in {
                "start": _format_datetime(payload.occurrence_period_start) if payload.occurrence_period_start else None,
                "end": _format_datetime(payload.occurrence_period_end) if payload.occurrence_period_end else None,
            }.items()
            if v is not None
        }

    if payload.condition:
        result["condition"] = _reference_with_identifier_from_payload(payload.condition)

    if payload.performer:
        result["performer"] = _reference_with_identifier_from_payload(payload.performer)

    if payload.method:
        result["method"] = payload_risk_assessment_codeable_concept(payload.method)

    if payload.code:
        result["code"] = payload_risk_assessment_codeable_concept(payload.code)

    if payload.reason_code:
        result["reasonCode"] = [
            payload_risk_assessment_codeable_concept(rc) for rc in payload.reason_code if rc
        ]

    if payload.reason_reference:
        result["reasonReference"] = [
            _reference_with_identifier_from_payload(rr) for rr in payload.reason_reference if rr
        ]

    if payload.basis:
        result["basis"] = [
            _reference_with_identifier_from_payload(b) for b in payload.basis if b
        ]

    if payload.prediction:
        result["prediction"] = [
            payload_risk_assessment_prediction(p) for p in payload.prediction if p
        ]

    if payload.mitigation:
        result["mitigation"] = payload.mitigation

    if payload.note:
        result["note"] = [payload_risk_assessment_note(n) for n in payload.note if n]

    if payload.identifier:
        result["identifier"] = [
            payload_risk_assessment_identifier(i) for i in payload.identifier if i
        ]

    if payload.extension:
        result["extension"] = list(payload.extension)

    return {k: v for k, v in result.items() if v is not None}


def patch_fragment_to_fhir_risk_assessment(
    payload: RiskAssessmentPatchSchema,
) -> tuple[dict[str, Any], set[str]]:
    """Convert a RiskAssessmentPatchSchema to a FHIR fragment and touched top-level field set."""
    provided = payload.model_fields_set
    fragment: dict[str, Any] = {}
    touched: set[str] = set()

    if "status" in provided:
        touched.add("status")
        fragment["status"] = (
            getattr(payload.status, "value", str(payload.status))
            if payload.status is not None
            else None
        )

    if "subject" in provided:
        touched.add("subject")
        fragment["subject"] = (
            _reference_with_identifier_from_payload(payload.subject)
            if payload.subject is not None
            else None
        )

    if "based_on" in provided:
        touched.add("basedOn")
        fragment["basedOn"] = (
            _reference_with_identifier_from_payload(payload.based_on)
            if payload.based_on is not None
            else None
        )

    if "parent" in provided:
        touched.add("parent")
        fragment["parent"] = (
            _reference_with_identifier_from_payload(payload.parent)
            if payload.parent is not None
            else None
        )

    if "encounter" in provided:
        touched.add("encounter")
        fragment["encounter"] = (
            _reference_with_identifier_from_payload(payload.encounter)
            if payload.encounter is not None
            else None
        )

    if "occurrence_date_time" in provided or "occurrence_period_start" in provided or "occurrence_period_end" in provided:
        touched.update({"occurrenceDateTime", "occurrencePeriod"})
        if payload.occurrence_date_time is not None:
            fragment["occurrenceDateTime"] = _format_datetime(payload.occurrence_date_time)
            fragment["occurrencePeriod"] = None
        elif payload.occurrence_period_start is not None or payload.occurrence_period_end is not None:
            fragment["occurrencePeriod"] = {
                k: v
                for k, v in {
                    "start": _format_datetime(payload.occurrence_period_start) if payload.occurrence_period_start else None,
                    "end": _format_datetime(payload.occurrence_period_end) if payload.occurrence_period_end else None,
                }.items()
                if v is not None
            }
            fragment["occurrenceDateTime"] = None
        else:
            fragment["occurrenceDateTime"] = None
            fragment["occurrencePeriod"] = None

    if "condition" in provided:
        touched.add("condition")
        fragment["condition"] = (
            _reference_with_identifier_from_payload(payload.condition)
            if payload.condition is not None
            else None
        )

    if "performer" in provided:
        touched.add("performer")
        fragment["performer"] = (
            _reference_with_identifier_from_payload(payload.performer)
            if payload.performer is not None
            else None
        )

    if "method" in provided:
        touched.add("method")
        fragment["method"] = (
            payload_risk_assessment_codeable_concept(payload.method)
            if payload.method is not None
            else None
        )

    if "code" in provided:
        touched.add("code")
        fragment["code"] = (
            payload_risk_assessment_codeable_concept(payload.code)
            if payload.code is not None
            else None
        )

    if "reason_code" in provided:
        touched.add("reasonCode")
        fragment["reasonCode"] = (
            [payload_risk_assessment_codeable_concept(rc) for rc in payload.reason_code if rc]
            if payload.reason_code is not None
            else None
        )

    if "reason_reference" in provided:
        touched.add("reasonReference")
        fragment["reasonReference"] = (
            [_reference_with_identifier_from_payload(rr) for rr in payload.reason_reference if rr]
            if payload.reason_reference is not None
            else None
        )

    if "basis" in provided:
        touched.add("basis")
        fragment["basis"] = (
            [_reference_with_identifier_from_payload(b) for b in payload.basis if b]
            if payload.basis is not None
            else None
        )

    if "prediction" in provided:
        touched.add("prediction")
        fragment["prediction"] = (
            [payload_risk_assessment_prediction(p) for p in payload.prediction if p]
            if payload.prediction is not None
            else None
        )

    if "mitigation" in provided:
        touched.add("mitigation")
        fragment["mitigation"] = payload.mitigation

    if "note" in provided:
        touched.add("note")
        fragment["note"] = (
            [payload_risk_assessment_note(n) for n in payload.note if n]
            if payload.note is not None
            else None
        )

    if "identifier" in provided:
        touched.add("identifier")
        fragment["identifier"] = (
            [payload_risk_assessment_identifier(i) for i in payload.identifier if i]
            if payload.identifier is not None
            else None
        )

    if "extension" in provided:
        touched.add("extension")
        fragment["extension"] = (
            list(payload.extension) if payload.extension is not None else None
        )

    return fragment, touched
