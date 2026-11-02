from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.immunization_recommendation import (
        ImmunizationRecommendationDateCriterionModel,
        ImmunizationRecommendationIdentifierModel,
        ImmunizationRecommendationModel,
        ImmunizationRecommendationRecommendationModel,
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


def fhir_immunization_recommendation_codeable_concept(codings, text: str | None) -> dict | None:
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


def fhir_immunization_recommendation_identifier(i: ImmunizationRecommendationIdentifierModel) -> dict:
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

    entry = {
        "use": fhir_enum(i.use) if i.use else None,
        "type": fhir_immunization_recommendation_codeable_concept(i.type_codings, i.type_text),
        "system": i.system,
        "value": i.value,
        "period": (
            {
                k: v
                for k, v in {
                    "start": fhir_instant(i.period_start) if i.period_start else None,
                    "end": fhir_instant(i.period_end) if i.period_end else None,
                }.items()
                if v is not None
            }
            if (i.period_start or i.period_end)
            else None
        ),
        "assigner": assigner_entry if assigner_entry else None,
    }
    return {k: v for k, v in entry.items() if v is not None}


def fhir_immunization_recommendation_date_criterion(
    dc: ImmunizationRecommendationDateCriterionModel,
) -> dict:
    entry = {
        "code": fhir_immunization_recommendation_codeable_concept(dc.code_codings, dc.code_text),
        "value": fhir_instant(dc.value),
    }
    return {k: v for k, v in entry.items() if v is not None}


def fhir_immunization_recommendation_recommendation(
    r: ImmunizationRecommendationRecommendationModel,
) -> dict:
    vc_list = [
        fhir_immunization_recommendation_codeable_concept(vc.codings, vc.text)
        for vc in r.vaccine_codes
    ] if r.vaccine_codes else None
    if vc_list:
        vc_list = [v for v in vc_list if v]

    cvc_list = [
        fhir_immunization_recommendation_codeable_concept(cvc.codings, cvc.text)
        for cvc in r.contraindicated_vaccine_codes
    ] if r.contraindicated_vaccine_codes else None
    if cvc_list:
        cvc_list = [v for v in cvc_list if v]

    fr_list = [
        fhir_immunization_recommendation_codeable_concept(fr.codings, fr.text)
        for fr in r.forecast_reasons
    ] if r.forecast_reasons else None
    if fr_list:
        fr_list = [v for v in fr_list if v]

    dc_list = [
        fhir_immunization_recommendation_date_criterion(dc)
        for dc in r.date_criteria
    ] if r.date_criteria else None
    if dc_list:
        dc_list = [v for v in dc_list if v]

    si_list = [
        _fhir_reference_with_identifier_fallback(si, "reference")
        for si in r.supporting_immunizations
    ] if r.supporting_immunizations else None
    if si_list:
        si_list = [v for v in si_list if v]

    spi_list = [
        _fhir_reference_with_identifier_fallback(spi, "reference")
        for spi in r.supporting_patient_information
    ] if r.supporting_patient_information else None
    if spi_list:
        spi_list = [v for v in spi_list if v]

    entry = {
        "vaccineCode": vc_list or None,
        "targetDisease": fhir_immunization_recommendation_codeable_concept(
            r.target_disease_codings, r.target_disease_text
        ),
        "contraindicatedVaccineCode": cvc_list or None,
        "forecastStatus": fhir_immunization_recommendation_codeable_concept(
            r.forecast_status_codings, r.forecast_status_text
        ),
        "forecastReason": fr_list or None,
        "dateCriterion": dc_list or None,
        "description": r.description,
        "series": r.series,
        "doseNumberPositiveInt": r.dose_number_positive_int,
        "doseNumberString": r.dose_number_string,
        "seriesDosesPositiveInt": r.series_doses_positive_int,
        "seriesDosesString": r.series_doses_string,
        "supportingImmunization": si_list or None,
        "supportingPatientInformation": spi_list or None,
    }
    return {k: v for k, v in entry.items() if v is not None}


def to_fhir_immunization_recommendation(
    model: ImmunizationRecommendationModel,
) -> dict:
    meta = {
        "versionId": "1",
        "lastUpdated": fhir_instant(model.updated_at or model.created_at),
    }

    identifiers = [
        fhir_immunization_recommendation_identifier(i) for i in model.identifiers
    ] if model.identifiers else None

    recommendations = [
        fhir_immunization_recommendation_recommendation(r)
        for r in model.recommendations
    ]

    patient = _fhir_reference_with_identifier_fallback(model, "patient")

    authority = (
        _fhir_reference_with_identifier_fallback(model, "authority")
        if (model.authority_reference or model.authority_id)
        else None
    )

    fhir_dict: dict = {
        "resourceType": "ImmunizationRecommendation",
        "id": str(model.immunization_recommendation_id),
        "meta": meta,
        "identifier": identifiers if identifiers else None,
        "patient": patient,
        "date": fhir_instant(model.date),
        "authority": authority,
        "recommendation": recommendations,
    }
    return {k: v for k, v in fhir_dict.items() if v is not None}
