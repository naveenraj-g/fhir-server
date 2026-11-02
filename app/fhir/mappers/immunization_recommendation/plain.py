from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.immunization_recommendation import (
        ImmunizationRecommendationDateCriterionModel,
        ImmunizationRecommendationIdentifierModel,
        ImmunizationRecommendationModel,
        ImmunizationRecommendationRecommendationModel,
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


def plain_immunization_recommendation_codeable_concept(codings, text: str | None) -> dict | None:
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
        "id": getattr(obj, "id", None),
        "reference": ref_str,
        "reference_display": display,
        "reference_identifier_use": fhir_enum(id_use) if id_use else None,
        "reference_identifier_type_system": getattr(obj, f"{prefix}_identifier_type_system", None),
        "reference_identifier_type_version": getattr(obj, f"{prefix}_identifier_type_version", None),
        "reference_identifier_type_code": getattr(obj, f"{prefix}_identifier_type_code", None),
        "reference_identifier_type_display": getattr(obj, f"{prefix}_identifier_type_display", None),
        "reference_identifier_type_user_selected": getattr(obj, f"{prefix}_identifier_type_user_selected", None),
        "reference_identifier_type_text": getattr(obj, f"{prefix}_identifier_type_text", None),
        "reference_identifier_system": getattr(obj, f"{prefix}_identifier_system", None),
        "reference_identifier_value": getattr(obj, f"{prefix}_identifier_value", None),
        "reference_identifier_period_start": getattr(obj, f"{prefix}_identifier_period_start", None),
        "reference_identifier_period_end": getattr(obj, f"{prefix}_identifier_period_end", None),
    }


def plain_immunization_recommendation_identifier(i: ImmunizationRecommendationIdentifierModel) -> dict:
    assigner_raw = getattr(i, "assigner_reference", None)
    assigner_id = getattr(i, "assigner_id", None)
    assigner_type = getattr(i, "assigner_type", None)
    assigner_str = assigner_raw
    if not assigner_str and assigner_type and assigner_id:
        assigner_str = f"{fhir_enum(assigner_type)}/{assigner_id}"

    return {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type": plain_immunization_recommendation_codeable_concept(i.type_codings, i.type_text),
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start,
        "period_end": i.period_end,
        "assigner": assigner_str,
        "assigner_display": getattr(i, "assigner_display", None),
        "assigner_identifier_use": (
            fhir_enum(i.assigner_identifier_use)
            if getattr(i, "assigner_identifier_use", None)
            else None
        ),
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


def plain_immunization_recommendation_date_criterion(
    dc: ImmunizationRecommendationDateCriterionModel,
) -> dict:
    return {
        "id": dc.id,
        "code": plain_immunization_recommendation_codeable_concept(dc.code_codings, dc.code_text),
        "value": dc.value,
    }


def plain_immunization_recommendation_recommendation(
    r: ImmunizationRecommendationRecommendationModel,
) -> dict:
    return {
        "id": r.id,
        "vaccine_code": (
            [
                plain_immunization_recommendation_codeable_concept(vc.codings, vc.text)
                for vc in r.vaccine_codes
            ]
            if r.vaccine_codes
            else None
        ),
        "target_disease": plain_immunization_recommendation_codeable_concept(
            r.target_disease_codings, r.target_disease_text
        ),
        "contraindicated_vaccine_code": (
            [
                plain_immunization_recommendation_codeable_concept(cvc.codings, cvc.text)
                for cvc in r.contraindicated_vaccine_codes
            ]
            if r.contraindicated_vaccine_codes
            else None
        ),
        "forecast_status": plain_immunization_recommendation_codeable_concept(
            r.forecast_status_codings, r.forecast_status_text
        ),
        "forecast_reason": (
            [
                plain_immunization_recommendation_codeable_concept(fr.codings, fr.text)
                for fr in r.forecast_reasons
            ]
            if r.forecast_reasons
            else None
        ),
        "date_criterion": (
            [
                plain_immunization_recommendation_date_criterion(dc)
                for dc in r.date_criteria
            ]
            if r.date_criteria
            else None
        ),
        "description": r.description,
        "series": r.series,
        "dose_number_positive_int": r.dose_number_positive_int,
        "dose_number_string": r.dose_number_string,
        "series_doses_positive_int": r.series_doses_positive_int,
        "series_doses_string": r.series_doses_string,
        "supporting_immunization": (
            [
                plain_reference_with_identifier_fallback(si, "reference")
                for si in r.supporting_immunizations
            ]
            if r.supporting_immunizations
            else None
        ),
        "supporting_patient_information": (
            [
                plain_reference_with_identifier_fallback(spi, "reference")
                for spi in r.supporting_patient_information
            ]
            if r.supporting_patient_information
            else None
        ),
    }


def to_plain_immunization_recommendation(
    model: ImmunizationRecommendationModel,
) -> dict:
    return {
        "id": model.immunization_recommendation_id,
        "identifier": (
            [plain_immunization_recommendation_identifier(i) for i in model.identifiers]
            if model.identifiers
            else None
        ),
        "patient": plain_reference_with_identifier_fallback(model, "patient"),
        "date": model.date,
        "authority": (
            plain_reference_with_identifier_fallback(model, "authority")
            if (model.authority_reference or model.authority_id)
            else None
        ),
        "recommendation": [
            plain_immunization_recommendation_recommendation(r)
            for r in model.recommendations
        ],
        "tenant_id": model.tenant_id,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
