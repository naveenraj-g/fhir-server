from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

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


def plain_coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
        }
        if any(v is not None for v in entry.values()):
            result.append(entry)
    return result


def plain_risk_assessment_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = plain_coding_list(codings)
    if not coding_list and not text:
        return None
    return {
        "coding": coding_list if coding_list else None,
        "text": text,
    }


def plain_reference_with_identifier_fallback(obj, prefix: str) -> dict:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    ref_str = raw_reference
    if not ref_str and ref_type and ref_id:
        ref_str = f"{fhir_enum(ref_type)}/{ref_id}"

    id_use = getattr(obj, f"{prefix}_identifier_use", None)

    return {
        "reference": ref_str,
        "type": fhir_enum(ref_type) if ref_type else None,
        "id": ref_id,
        "display": display,
        "identifier_use": fhir_enum(id_use) if id_use else None,
        "identifier_type_system": getattr(obj, f"{prefix}_identifier_type_system", None),
        "identifier_type_version": getattr(obj, f"{prefix}_identifier_type_version", None),
        "identifier_type_code": getattr(obj, f"{prefix}_identifier_type_code", None),
        "identifier_type_display": getattr(obj, f"{prefix}_identifier_type_display", None),
        "identifier_type_user_selected": getattr(obj, f"{prefix}_identifier_type_user_selected", None),
        "identifier_type_text": getattr(obj, f"{prefix}_identifier_type_text", None),
        "identifier_system": getattr(obj, f"{prefix}_identifier_system", None),
        "identifier_value": getattr(obj, f"{prefix}_identifier_value", None),
        "identifier_period_start": getattr(obj, f"{prefix}_identifier_period_start", None),
        "identifier_period_end": getattr(obj, f"{prefix}_identifier_period_end", None),
    }


def plain_risk_assessment_identifier(i: RiskAssessmentIdentifierModel) -> dict:
    assigner_raw = getattr(i, "assigner_reference", None)
    assigner_id = getattr(i, "assigner_id", None)
    assigner_type = getattr(i, "assigner_type", None)
    assigner_display = getattr(i, "assigner_display", None)
    assigner_ref_str = assigner_raw
    if not assigner_ref_str and assigner_type and assigner_id:
        assigner_ref_str = f"{fhir_enum(assigner_type)}/{assigner_id}"

    assigner_id_use = getattr(i, "assigner_identifier_use", None)

    type_cc = plain_risk_assessment_codeable_concept(
        getattr(i, "type_codings", None), getattr(i, "type_text", None)
    )

    return {
        "id": i.id,
        "use": fhir_enum(i.use) if getattr(i, "use", None) else None,
        "type": type_cc,
        "system": getattr(i, "system", None),
        "value": getattr(i, "value", None),
        "period_start": getattr(i, "period_start", None),
        "period_end": getattr(i, "period_end", None),
        "assigner_reference": assigner_ref_str,
        "assigner_type": fhir_enum(assigner_type) if assigner_type else None,
        "assigner_id": assigner_id,
        "assigner_display": assigner_display,
        "assigner_identifier_use": fhir_enum(assigner_id_use) if assigner_id_use else None,
        "assigner_identifier_type_system": getattr(i, "assigner_identifier_type_system", None),
        "assigner_identifier_type_version": getattr(i, "assigner_identifier_type_version", None),
        "assigner_identifier_type_code": getattr(i, "assigner_identifier_type_code", None),
        "assigner_identifier_type_display": getattr(i, "assigner_identifier_type_display", None),
        "assigner_identifier_type_user_selected": getattr(i, "assigner_identifier_type_user_selected", None),
        "assigner_identifier_type_text": getattr(i, "assigner_identifier_type_text", None),
        "assigner_identifier_system": getattr(i, "assigner_identifier_system", None),
        "assigner_identifier_value": getattr(i, "assigner_identifier_value", None),
        "assigner_identifier_period_start": getattr(i, "assigner_identifier_period_start", None),
        "assigner_identifier_period_end": getattr(i, "assigner_identifier_period_end", None),
    }


def plain_risk_assessment_note(n: RiskAssessmentNoteModel) -> dict:
    author_raw = getattr(n, "author_reference", None)
    author_type = getattr(n, "author_type", None)
    author_id = getattr(n, "author_id", None)
    author_ref_str = author_raw
    if not author_ref_str and author_type and author_id:
        author_ref_str = f"{fhir_enum(author_type)}/{author_id}"

    author_id_use = getattr(n, "author_identifier_use", None)

    return {
        "id": n.id,
        "text": n.text,
        "time": n.time,
        "author_string": n.author_string,
        "author_reference": author_ref_str,
        "author_display": n.author_display,
        "author_identifier_use": fhir_enum(author_id_use) if author_id_use else None,
        "author_identifier_type_system": getattr(n, "author_identifier_type_system", None),
        "author_identifier_type_version": getattr(n, "author_identifier_type_version", None),
        "author_identifier_type_code": getattr(n, "author_identifier_type_code", None),
        "author_identifier_type_display": getattr(n, "author_identifier_type_display", None),
        "author_identifier_type_user_selected": getattr(n, "author_identifier_type_user_selected", None),
        "author_identifier_type_text": getattr(n, "author_identifier_type_text", None),
        "author_identifier_system": getattr(n, "author_identifier_system", None),
        "author_identifier_value": getattr(n, "author_identifier_value", None),
        "author_identifier_period_start": getattr(n, "author_identifier_period_start", None),
        "author_identifier_period_end": getattr(n, "author_identifier_period_end", None),
    }


def plain_risk_assessment_prediction(p: RiskAssessmentPredictionModel) -> dict:
    outcome = plain_risk_assessment_codeable_concept(
        getattr(p, "outcome_codings", None), getattr(p, "outcome_text", None)
    )
    qualitative_risk = plain_risk_assessment_codeable_concept(
        getattr(p, "qualitative_risk_codings", None), getattr(p, "qualitative_risk_text", None)
    )

    prob_range = None
    if (
        getattr(p, "probability_range_low_value", None) is not None
        or getattr(p, "probability_range_high_value", None) is not None
    ):
        low_dict = None
        if getattr(p, "probability_range_low_value", None) is not None:
            low_dict = {
                "value": float(p.probability_range_low_value),
                "unit": p.probability_range_low_unit,
                "system": p.probability_range_low_system,
                "code": p.probability_range_low_code,
            }
        high_dict = None
        if getattr(p, "probability_range_high_value", None) is not None:
            high_dict = {
                "value": float(p.probability_range_high_value),
                "unit": p.probability_range_high_unit,
                "system": p.probability_range_high_system,
                "code": p.probability_range_high_code,
            }
        prob_range = {"low": low_dict, "high": high_dict}

    when_range = None
    if (
        getattr(p, "when_range_low_value", None) is not None
        or getattr(p, "when_range_high_value", None) is not None
    ):
        low_dict = None
        if getattr(p, "when_range_low_value", None) is not None:
            low_dict = {
                "value": float(p.when_range_low_value),
                "unit": p.when_range_low_unit,
                "system": p.when_range_low_system,
                "code": p.when_range_low_code,
            }
        high_dict = None
        if getattr(p, "when_range_high_value", None) is not None:
            high_dict = {
                "value": float(p.when_range_high_value),
                "unit": p.when_range_high_unit,
                "system": p.when_range_high_system,
                "code": p.when_range_high_code,
            }
        when_range = {"low": low_dict, "high": high_dict}

    return {
        "id": p.id,
        "outcome": outcome,
        "probability_decimal": float(p.probability_decimal) if getattr(p, "probability_decimal", None) is not None else None,
        "probability_range": prob_range,
        "qualitative_risk": qualitative_risk,
        "relative_risk": float(p.relative_risk) if getattr(p, "relative_risk", None) is not None else None,
        "when_period_start": getattr(p, "when_period_start", None),
        "when_period_end": getattr(p, "when_period_end", None),
        "when_range": when_range,
        "rationale": getattr(p, "rationale", None),
    }


def to_plain_risk_assessment(model: RiskAssessmentModel) -> dict:
    """Convert a RiskAssessmentModel ORM instance to a plain snake_case dict."""
    reason_codes = []
    for rc in getattr(model, "reason_codes", []) or []:
        cc = plain_risk_assessment_codeable_concept(getattr(rc, "codings", None), getattr(rc, "text", None))
        if cc:
            reason_codes.append(cc)

    reason_refs = [
        plain_reference_with_identifier_fallback(rr, "reference")
        for rr in getattr(model, "reason_references", []) or []
    ]

    bases = [
        plain_reference_with_identifier_fallback(b, "reference")
        for b in getattr(model, "basis", []) or []
    ]

    predictions = [
        plain_risk_assessment_prediction(p)
        for p in getattr(model, "predictions", []) or []
    ]

    notes = [
        plain_risk_assessment_note(n)
        for n in getattr(model, "notes", []) or []
    ]

    identifiers = [
        plain_risk_assessment_identifier(i)
        for i in getattr(model, "identifiers", []) or []
    ]

    return {
        "id": model.risk_assessment_id,
        "status": fhir_enum(model.status),
        "method": plain_risk_assessment_codeable_concept(
            getattr(model, "method_codings", None), getattr(model, "method_text", None)
        ),
        "code": plain_risk_assessment_codeable_concept(
            getattr(model, "code_codings", None), getattr(model, "code_text", None)
        ),
        "subject": plain_reference_with_identifier_fallback(model, "subject"),
        "based_on": (
            plain_reference_with_identifier_fallback(model, "based_on")
            if (model.based_on_reference or model.based_on_id or model.based_on_identifier_value)
            else None
        ),
        "parent": (
            plain_reference_with_identifier_fallback(model, "parent")
            if (model.parent_reference or model.parent_id or model.parent_identifier_value)
            else None
        ),
        "encounter": (
            plain_reference_with_identifier_fallback(model, "encounter")
            if (model.encounter_reference or model.encounter_id or model.encounter_identifier_value)
            else None
        ),
        "occurrence_date_time": getattr(model, "occurrence_date_time", None),
        "occurrence_period_start": getattr(model, "occurrence_period_start", None),
        "occurrence_period_end": getattr(model, "occurrence_period_end", None),
        "condition": (
            plain_reference_with_identifier_fallback(model, "condition")
            if (model.condition_reference or model.condition_id or model.condition_identifier_value)
            else None
        ),
        "performer": (
            plain_reference_with_identifier_fallback(model, "performer")
            if (model.performer_reference or model.performer_id or model.performer_identifier_value)
            else None
        ),
        "reason_code": reason_codes if reason_codes else None,
        "reason_reference": reason_refs if reason_refs else None,
        "basis": bases if bases else None,
        "prediction": predictions if predictions else None,
        "mitigation": getattr(model, "mitigation", None),
        "note": notes if notes else None,
        "identifier": identifiers if identifiers else None,
        "extension": list(model.extension) if getattr(model, "extension", None) else None,
        "created_at": getattr(model, "created_at", None),
        "updated_at": getattr(model, "updated_at", None),
        "created_by": getattr(model, "created_by", None),
        "updated_by": getattr(model, "updated_by", None),
    }
