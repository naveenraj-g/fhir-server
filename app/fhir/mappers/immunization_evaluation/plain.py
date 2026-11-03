from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.immunization_evaluation import (
        ImmunizationEvaluationDoseStatusReasonModel,
        ImmunizationEvaluationIdentifierModel,
        ImmunizationEvaluationModel,
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


def plain_immunization_evaluation_codeable_concept(
    codings, text: str | None
) -> dict | None:
    coding_list = plain_coding_list(codings)
    if not coding_list and not text:
        return None
    return {
        "coding": coding_list if coding_list else None,
        "text": text,
    }


def plain_reference_with_identifier_fallback(obj, prefix: str) -> dict:
    ref_col = prefix if prefix.endswith("reference") else f"{prefix}_reference"
    disp_col = "display" if prefix == "reference" else f"{prefix}_display"
    type_col = f"{prefix}_type"
    id_col = f"{prefix}_id"

    raw_reference = getattr(obj, ref_col, None)
    ref_type = getattr(obj, type_col, None)
    ref_id = getattr(obj, id_col, None)
    display = getattr(obj, disp_col, None)

    ref_str = raw_reference
    if not ref_str and ref_type and ref_id:
        ref_str = f"{fhir_enum(ref_type)}/{ref_id}"

    id_prefix = "" if prefix == "reference" else f"{prefix}_"
    id_use = getattr(obj, f"{id_prefix}identifier_use", None)

    return {
        "reference": ref_str,
        "display": display,
        "identifier_use": fhir_enum(id_use) if id_use else None,
        "identifier_type_system": getattr(obj, f"{id_prefix}identifier_type_system", None),
        "identifier_type_version": getattr(obj, f"{id_prefix}identifier_type_version", None),
        "identifier_type_code": getattr(obj, f"{id_prefix}identifier_type_code", None),
        "identifier_type_display": getattr(obj, f"{id_prefix}identifier_type_display", None),
        "identifier_type_user_selected": getattr(obj, f"{id_prefix}identifier_type_user_selected", None),
        "identifier_type_text": getattr(obj, f"{id_prefix}identifier_type_text", None),
        "identifier_system": getattr(obj, f"{id_prefix}identifier_system", None),
        "identifier_value": getattr(obj, f"{id_prefix}identifier_value", None),
        "identifier_period_start": getattr(obj, f"{id_prefix}identifier_period_start", None),
        "identifier_period_end": getattr(obj, f"{id_prefix}identifier_period_end", None),
    }


def plain_immunization_evaluation_identifier(i: ImmunizationEvaluationIdentifierModel) -> dict:
    assigner_raw = getattr(i, "assigner_reference", None)
    assigner_id = getattr(i, "assigner_id", None)
    assigner_type = getattr(i, "assigner_type", None)
    assigner_display = getattr(i, "assigner_display", None)
    assigner_ref_str = assigner_raw
    if not assigner_ref_str and assigner_type and assigner_id:
        assigner_ref_str = f"{fhir_enum(assigner_type)}/{assigner_id}"

    assigner_id_use = getattr(i, "assigner_identifier_use", None)

    type_cc = plain_immunization_evaluation_codeable_concept(
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
        "assigner": assigner_ref_str,
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


def plain_immunization_evaluation_dose_status_reason(
    r: ImmunizationEvaluationDoseStatusReasonModel,
) -> dict:
    codings = plain_coding_list(getattr(r, "codings", None))
    return {
        "id": r.id,
        "text": getattr(r, "text", None),
        "coding": codings if codings else None,
    }


def to_plain_immunization_evaluation(model: ImmunizationEvaluationModel) -> dict:
    """Serializes an ImmunizationEvaluationModel ORM row to a plain snake_case dict."""
    target_disease = plain_immunization_evaluation_codeable_concept(
        getattr(model, "target_disease_codings", None), model.target_disease_text
    ) or {"text": model.target_disease_text, "coding": None}

    dose_status = plain_immunization_evaluation_codeable_concept(
        getattr(model, "dose_status_codings", None), model.dose_status_text
    ) or {"text": model.dose_status_text, "coding": None}

    identifiers = [
        plain_immunization_evaluation_identifier(i)
        for i in getattr(model, "identifiers", []) or []
    ]

    reasons = [
        plain_immunization_evaluation_dose_status_reason(r)
        for r in getattr(model, "dose_status_reasons", []) or []
    ]

    patient = plain_reference_with_identifier_fallback(model, "patient")
    authority = plain_reference_with_identifier_fallback(model, "authority")
    immunization_event = plain_reference_with_identifier_fallback(
        model, "immunization_event"
    )

    has_authority = any(v is not None for v in authority.values())

    return {
        "id": model.immunization_evaluation_id,
        "status": fhir_enum(model.status),
        "patient": patient,
        "date": model.date,
        "authority": authority if has_authority else None,
        "target_disease": target_disease,
        "immunization_event": immunization_event,
        "dose_status": dose_status,
        "dose_status_reason": reasons if reasons else None,
        "description": model.description,
        "series": model.series,
        "dose_number_positive_int": model.dose_number_positive_int,
        "dose_number_string": model.dose_number_string,
        "series_doses_positive_int": model.series_doses_positive_int,
        "series_doses_string": model.series_doses_string,
        "identifier": identifiers if identifiers else None,
        "extension": model.extension if getattr(model, "extension", None) else None,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
    }
