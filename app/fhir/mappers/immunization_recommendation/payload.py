"""Payload -> FHIR JSON conversion for ImmunizationRecommendation.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(ImmunizationRecommendationCreateSchema / ImmunizationRecommendationPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.schemas.immunization_recommendation.input import (
        ImmunizationRecommendationCodeableConceptInput,
        ImmunizationRecommendationCreateSchema,
        ImmunizationRecommendationDateCriterionInput,
        ImmunizationRecommendationIdentifierInput,
        ImmunizationRecommendationPatchSchema,
        ImmunizationRecommendationRecommendationInput,
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


def payload_immunization_recommendation_codeable_concept(
    cc: ImmunizationRecommendationCodeableConceptInput | dict | None,
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
                    "start": _format_datetime(id_period_start),
                    "end": _format_datetime(id_period_end),
                }.items()
                if v is not None
            }
        entry["identifier"] = identifier

    return entry


def payload_immunization_recommendation_identifier(
    ident: ImmunizationRecommendationIdentifierInput | dict,
) -> dict:
    use = _val(ident, "use")
    raw_type = _val(ident, "type")
    type_cc = payload_immunization_recommendation_codeable_concept(raw_type)
    system = _val(ident, "system")
    value = _val(ident, "value")
    start = _val(ident, "period_start")
    end = _val(ident, "period_end")

    assigner_raw = _val(ident, "assigner")
    assigner_display = _val(ident, "assigner_display")
    assigner_entry: dict = {}
    if assigner_raw:
        assigner_entry["reference"] = assigner_raw
    if assigner_display:
        assigner_entry["display"] = assigner_display

    assigner_id_use = _val(ident, "assigner_identifier_use")
    assigner_id_system = _val(ident, "assigner_identifier_system")
    assigner_id_value = _val(ident, "assigner_identifier_value")
    if assigner_id_use or assigner_id_system or assigner_id_value:
        assigner_identifier: dict = {}
        if assigner_id_use:
            assigner_identifier["use"] = getattr(assigner_id_use, "value", str(assigner_id_use))
        if assigner_id_system:
            assigner_identifier["system"] = assigner_id_system
        if assigner_id_value:
            assigner_identifier["value"] = assigner_id_value
        assigner_entry["identifier"] = assigner_identifier

    entry = {
        "use": getattr(use, "value", str(use)) if use else None,
        "type": type_cc,
        "system": system,
        "value": value,
        "period": (
            {
                k: v
                for k, v in {
                    "start": _format_datetime(start),
                    "end": _format_datetime(end),
                }.items()
                if v is not None
            }
            if (start or end)
            else None
        ),
        "assigner": assigner_entry if assigner_entry else None,
    }
    return {k: v for k, v in entry.items() if v is not None}


def payload_immunization_recommendation_date_criterion(
    dc: ImmunizationRecommendationDateCriterionInput | dict,
) -> dict:
    code_cc = payload_immunization_recommendation_codeable_concept(_val(dc, "code"))
    value = _val(dc, "value")
    entry = {
        "code": code_cc,
        "value": _format_datetime(value),
    }
    return {k: v for k, v in entry.items() if v is not None}


def payload_immunization_recommendation_recommendation(
    r: ImmunizationRecommendationRecommendationInput | dict,
) -> dict:
    vc_in = _val(r, "vaccine_code") or []
    vc_list = [payload_immunization_recommendation_codeable_concept(vc) for vc in vc_in]
    vc_list = [v for v in vc_list if v]

    td_cc = payload_immunization_recommendation_codeable_concept(_val(r, "target_disease"))

    cvc_in = _val(r, "contraindicated_vaccine_code") or []
    cvc_list = [payload_immunization_recommendation_codeable_concept(cvc) for cvc in cvc_in]
    cvc_list = [v for v in cvc_list if v]

    fs_cc = payload_immunization_recommendation_codeable_concept(_val(r, "forecast_status"))

    fr_in = _val(r, "forecast_reason") or []
    fr_list = [payload_immunization_recommendation_codeable_concept(fr) for fr in fr_in]
    fr_list = [v for v in fr_list if v]

    dc_in = _val(r, "date_criterion") or []
    dc_list = [payload_immunization_recommendation_date_criterion(dc) for dc in dc_in]
    dc_list = [v for v in dc_list if v]

    si_in = _val(r, "supporting_immunization") or []
    si_list = [_reference_with_identifier_from_payload(si) for si in si_in]
    si_list = [v for v in si_list if v]

    spi_in = _val(r, "supporting_patient_information") or []
    spi_list = [_reference_with_identifier_from_payload(spi) for spi in spi_in]
    spi_list = [v for v in spi_list if v]

    entry = {
        "vaccineCode": vc_list or None,
        "targetDisease": td_cc,
        "contraindicatedVaccineCode": cvc_list or None,
        "forecastStatus": fs_cc,
        "forecastReason": fr_list or None,
        "dateCriterion": dc_list or None,
        "description": _val(r, "description"),
        "series": _val(r, "series"),
        "doseNumberPositiveInt": _val(r, "dose_number_positive_int"),
        "doseNumberString": _val(r, "dose_number_string"),
        "seriesDosesPositiveInt": _val(r, "series_doses_positive_int"),
        "seriesDosesString": _val(r, "series_doses_string"),
        "supportingImmunization": si_list or None,
        "supportingPatientInformation": spi_list or None,
    }
    return {k: v for k, v in entry.items() if v is not None}


def payload_to_fhir_immunization_recommendation(
    payload: ImmunizationRecommendationCreateSchema | dict,
) -> dict:
    patient = _reference_with_identifier_from_payload(_val(payload, "patient"))
    authority = _reference_with_identifier_from_payload(_val(payload, "authority"))
    date_val = _val(payload, "date")

    idents_in = _val(payload, "identifier") or []
    identifiers = [payload_immunization_recommendation_identifier(i) for i in idents_in]
    identifiers = [i for i in identifiers if i]

    recs_in = _val(payload, "recommendation") or []
    recommendations = [
        payload_immunization_recommendation_recommendation(r) for r in recs_in
    ]

    fhir_dict: dict = {
        "resourceType": "ImmunizationRecommendation",
        "identifier": identifiers or None,
        "patient": patient,
        "date": _format_datetime(date_val),
        "authority": authority or None,
        "recommendation": recommendations,
    }
    return {k: v for k, v in fhir_dict.items() if v is not None}


def patch_fragment_to_fhir_immunization_recommendation(
    patch: ImmunizationRecommendationPatchSchema | dict,
) -> tuple[dict, set[str]]:
    data = (
        patch.model_dump(exclude_unset=True)
        if hasattr(patch, "model_dump")
        else dict(patch)
    )

    fragment: dict = {}
    touched: set[str] = set()

    for field, val in data.items():
        if field == "patient":
            touched.add("patient")
            fragment["patient"] = _reference_with_identifier_from_payload(val)

        elif field == "date":
            touched.add("date")
            fragment["date"] = _format_datetime(val)

        elif field == "authority":
            touched.add("authority")
            if val is not None:
                fragment["authority"] = _reference_with_identifier_from_payload(val)

        elif field == "identifier":
            touched.add("identifier")
            if val is not None:
                fragment["identifier"] = [
                    payload_immunization_recommendation_identifier(i) for i in val
                ]

        elif field == "recommendation":
            touched.add("recommendation")
            if val is not None:
                fragment["recommendation"] = [
                    payload_immunization_recommendation_recommendation(r) for r in val
                ]

    return fragment, touched
