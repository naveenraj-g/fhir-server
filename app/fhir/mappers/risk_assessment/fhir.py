from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.risk_assessment import (
        RiskAssessmentBasisModel,
        RiskAssessmentIdentifierModel,
        RiskAssessmentModel,
        RiskAssessmentNoteModel,
        RiskAssessmentPredictionModel,
        RiskAssessmentReasonCodeModel,
        RiskAssessmentReasonReferenceModel,
    )


def _fhir_coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            k: v
            for k, v in {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "userSelected": c.user_selected,
            }.items()
            if v is not None
        }
        if entry:
            result.append(entry)
    return result


def fhir_risk_assessment_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    elif ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_user_selected = getattr(obj, f"{prefix}_identifier_type_user_selected", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

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
            identifier["use"] = fhir_enum(id_use)
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
                    "start": fhir_instant(id_period_start) if id_period_start else None,
                    "end": fhir_instant(id_period_end) if id_period_end else None,
                }.items()
                if v is not None
            }
        entry["identifier"] = identifier

    return entry


def fhir_risk_assessment_identifier(i: RiskAssessmentIdentifierModel) -> dict:
    assigner_raw = getattr(i, "assigner_reference", None)
    assigner_id = getattr(i, "assigner_id", None)
    assigner_type = getattr(i, "assigner_type", None)
    assigner_display = getattr(i, "assigner_display", None)

    assigner_entry: dict = {}
    if assigner_raw:
        assigner_entry["reference"] = assigner_raw
    elif assigner_type and assigner_id:
        assigner_entry["reference"] = f"{fhir_enum(assigner_type)}/{assigner_id}"
    if assigner_display:
        assigner_entry["display"] = assigner_display

    assigner_id_use = getattr(i, "assigner_identifier_use", None)
    assigner_id_system = getattr(i, "assigner_identifier_system", None)
    assigner_id_value = getattr(i, "assigner_identifier_value", None)
    if assigner_id_use or assigner_id_system or assigner_id_value:
        assigner_identifier: dict = {}
        if assigner_id_use:
            assigner_identifier["use"] = fhir_enum(assigner_id_use)
        if assigner_id_system:
            assigner_identifier["system"] = assigner_id_system
        if assigner_id_value:
            assigner_identifier["value"] = assigner_id_value
        assigner_entry["identifier"] = assigner_identifier

    type_cc = fhir_risk_assessment_codeable_concept(
        getattr(i, "type_codings", None), getattr(i, "type_text", None)
    )

    period = None
    if getattr(i, "period_start", None) or getattr(i, "period_end", None):
        period = {
            k: v
            for k, v in {
                "start": fhir_instant(i.period_start) if getattr(i, "period_start", None) else None,
                "end": fhir_instant(i.period_end) if getattr(i, "period_end", None) else None,
            }.items()
            if v is not None
        }

    return {
        k: v
        for k, v in {
            "use": fhir_enum(i.use) if getattr(i, "use", None) else None,
            "type": type_cc,
            "system": getattr(i, "system", None),
            "value": getattr(i, "value", None),
            "period": period,
            "assigner": assigner_entry or None,
        }.items()
        if v is not None
    }


def fhir_risk_assessment_note(n: RiskAssessmentNoteModel) -> dict:
    author_ref = _fhir_reference_with_identifier_fallback(n, "author")
    entry: dict[str, Any] = {
        "text": n.text,
    }
    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.author_string:
        entry["authorString"] = n.author_string
    elif author_ref:
        entry["authorReference"] = author_ref
    return entry


def fhir_risk_assessment_prediction(p: RiskAssessmentPredictionModel) -> dict:
    outcome = fhir_risk_assessment_codeable_concept(
        getattr(p, "outcome_codings", None), getattr(p, "outcome_text", None)
    )
    qualitative_risk = fhir_risk_assessment_codeable_concept(
        getattr(p, "qualitative_risk_codings", None), getattr(p, "qualitative_risk_text", None)
    )

    pred: dict[str, Any] = {}
    if outcome:
        pred["outcome"] = outcome

    # probability[x]
    if getattr(p, "probability_decimal", None) is not None:
        pred["probabilityDecimal"] = float(p.probability_decimal)
    else:
        prob_range: dict[str, Any] = {}
        if getattr(p, "probability_range_low_value", None) is not None:
            prob_range["low"] = {
                k: v
                for k, v in {
                    "value": float(p.probability_range_low_value),
                    "unit": p.probability_range_low_unit,
                    "system": p.probability_range_low_system,
                    "code": p.probability_range_low_code,
                }.items()
                if v is not None
            }
        if getattr(p, "probability_range_high_value", None) is not None:
            prob_range["high"] = {
                k: v
                for k, v in {
                    "value": float(p.probability_range_high_value),
                    "unit": p.probability_range_high_unit,
                    "system": p.probability_range_high_system,
                    "code": p.probability_range_high_code,
                }.items()
                if v is not None
            }
        if prob_range:
            pred["probabilityRange"] = prob_range

    if qualitative_risk:
        pred["qualitativeRisk"] = qualitative_risk

    if getattr(p, "relative_risk", None) is not None:
        pred["relativeRisk"] = float(p.relative_risk)

    # when[x]
    if getattr(p, "when_period_start", None) or getattr(p, "when_period_end", None):
        pred["whenPeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(p.when_period_start) if p.when_period_start else None,
                "end": fhir_instant(p.when_period_end) if p.when_period_end else None,
            }.items()
            if v is not None
        }
    else:
        when_range: dict[str, Any] = {}
        if getattr(p, "when_range_low_value", None) is not None:
            when_range["low"] = {
                k: v
                for k, v in {
                    "value": float(p.when_range_low_value),
                    "unit": p.when_range_low_unit,
                    "system": p.when_range_low_system,
                    "code": p.when_range_low_code,
                }.items()
                if v is not None
            }
        if getattr(p, "when_range_high_value", None) is not None:
            when_range["high"] = {
                k: v
                for k, v in {
                    "value": float(p.when_range_high_value),
                    "unit": p.when_range_high_unit,
                    "system": p.when_range_high_system,
                    "code": p.when_range_high_code,
                }.items()
                if v is not None
            }
        if when_range:
            pred["whenRange"] = when_range

    if getattr(p, "rationale", None):
        pred["rationale"] = p.rationale

    return pred


def _fhir_meta(model: RiskAssessmentModel) -> dict:
    meta: dict = {}
    if getattr(model, "updated_at", None):
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    elif getattr(model, "created_at", None):
        meta["lastUpdated"] = fhir_instant(model.created_at)
    return meta


def to_fhir_risk_assessment(model: RiskAssessmentModel) -> dict:
    """Convert a RiskAssessmentModel ORM instance to a FHIR R4 JSON dict."""
    result: dict[str, Any] = {
        "resourceType": "RiskAssessment",
        "id": str(model.risk_assessment_id),
        "status": fhir_enum(model.status),
    }

    meta = _fhir_meta(model)
    if meta:
        result["meta"] = meta

    if getattr(model, "extension", None):
        result["extension"] = list(model.extension)

    # Identifiers
    identifiers = [fhir_risk_assessment_identifier(i) for i in getattr(model, "identifiers", []) or []]
    if identifiers:
        result["identifier"] = identifiers

    # Subject (required)
    subj_ref = _fhir_reference_with_identifier_fallback(model, "subject")
    if subj_ref:
        result["subject"] = subj_ref

    # basedOn
    based_on_ref = _fhir_reference_with_identifier_fallback(model, "based_on")
    if based_on_ref:
        result["basedOn"] = based_on_ref

    # parent
    parent_ref = _fhir_reference_with_identifier_fallback(model, "parent")
    if parent_ref:
        result["parent"] = parent_ref

    # encounter
    encounter_ref = _fhir_reference_with_identifier_fallback(model, "encounter")
    if encounter_ref:
        result["encounter"] = encounter_ref

    # occurrence[x]
    if getattr(model, "occurrence_date_time", None):
        result["occurrenceDateTime"] = fhir_instant(model.occurrence_date_time)
    elif getattr(model, "occurrence_period_start", None) or getattr(model, "occurrence_period_end", None):
        result["occurrencePeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(model.occurrence_period_start) if model.occurrence_period_start else None,
                "end": fhir_instant(model.occurrence_period_end) if model.occurrence_period_end else None,
            }.items()
            if v is not None
        }

    # condition
    condition_ref = _fhir_reference_with_identifier_fallback(model, "condition")
    if condition_ref:
        result["condition"] = condition_ref

    # performer
    performer_ref = _fhir_reference_with_identifier_fallback(model, "performer")
    if performer_ref:
        result["performer"] = performer_ref

    # method
    method = fhir_risk_assessment_codeable_concept(
        getattr(model, "method_codings", None), getattr(model, "method_text", None)
    )
    if method:
        result["method"] = method

    # code
    code = fhir_risk_assessment_codeable_concept(
        getattr(model, "code_codings", None), getattr(model, "code_text", None)
    )
    if code:
        result["code"] = code

    # reasonCode
    reason_codes = []
    for rc in getattr(model, "reason_codes", []) or []:
        cc = fhir_risk_assessment_codeable_concept(getattr(rc, "codings", None), getattr(rc, "text", None))
        if cc:
            reason_codes.append(cc)
    if reason_codes:
        result["reasonCode"] = reason_codes

    # reasonReference
    reason_refs = []
    for rr in getattr(model, "reason_references", []) or []:
        ref = _fhir_reference_with_identifier_fallback(rr, "reference")
        if ref:
            reason_refs.append(ref)
    if reason_refs:
        result["reasonReference"] = reason_refs

    # basis
    bases = []
    for b in getattr(model, "basis", []) or []:
        ref = _fhir_reference_with_identifier_fallback(b, "reference")
        if ref:
            bases.append(ref)
    if bases:
        result["basis"] = bases

    # prediction
    predictions = [fhir_risk_assessment_prediction(p) for p in getattr(model, "predictions", []) or []]
    if predictions:
        result["prediction"] = predictions

    # mitigation
    if getattr(model, "mitigation", None):
        result["mitigation"] = model.mitigation

    # note
    notes = [fhir_risk_assessment_note(n) for n in getattr(model, "notes", []) or []]
    if notes:
        result["note"] = notes

    return {k: v for k, v in result.items() if v is not None}
