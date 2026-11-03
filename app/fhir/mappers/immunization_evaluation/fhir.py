from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.immunization_evaluation import (
        ImmunizationEvaluationDoseStatusReasonModel,
        ImmunizationEvaluationIdentifierModel,
        ImmunizationEvaluationModel,
    )


def _fhir_meta(m: ImmunizationEvaluationModel) -> dict | None:
    meta: dict[str, Any] = {}
    if m.updated_at:
        meta["lastUpdated"] = fhir_instant(m.updated_at)
    return meta or None


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


def fhir_immunization_evaluation_codeable_concept(
    codings, text: str | None
) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict | None:
    ref_col = prefix if prefix.endswith("reference") else f"{prefix}_reference"
    disp_col = "display" if prefix == "reference" else f"{prefix}_display"
    type_col = f"{prefix}_type"
    id_col = f"{prefix}_id"

    raw_reference = getattr(obj, ref_col, None)
    ref_type = getattr(obj, type_col, None)
    ref_id = getattr(obj, id_col, None)
    display = getattr(obj, disp_col, None)

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    elif ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display

    id_prefix = "" if prefix == "reference" else f"{prefix}_"
    id_use = getattr(obj, f"{id_prefix}identifier_use", None)
    id_type_system = getattr(obj, f"{id_prefix}identifier_type_system", None)
    id_type_version = getattr(obj, f"{id_prefix}identifier_type_version", None)
    id_type_code = getattr(obj, f"{id_prefix}identifier_type_code", None)
    id_type_display = getattr(obj, f"{id_prefix}identifier_type_display", None)
    id_type_user_selected = getattr(obj, f"{id_prefix}identifier_type_user_selected", None)
    id_type_text = getattr(obj, f"{id_prefix}identifier_type_text", None)
    id_system = getattr(obj, f"{id_prefix}identifier_system", None)
    id_value = getattr(obj, f"{id_prefix}identifier_value", None)
    id_period_start = getattr(obj, f"{id_prefix}identifier_period_start", None)
    id_period_end = getattr(obj, f"{id_prefix}identifier_period_end", None)

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
            or id_type_display
            or id_type_text
            or id_type_version
            or id_type_user_selected
        ):
            type_coding: dict = {}
            if id_type_system:
                type_coding["system"] = id_type_system
            if id_type_version:
                type_coding["version"] = id_type_version
            if id_type_code:
                type_coding["code"] = id_type_code
            if id_type_display:
                type_coding["display"] = id_type_display
            if id_type_user_selected is not None:
                type_coding["userSelected"] = id_type_user_selected
            type_cc: dict = {}
            if type_coding:
                type_cc["coding"] = [type_coding]
            if id_type_text:
                type_cc["text"] = id_type_text
            if type_cc:
                identifier["type"] = type_cc
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_period_start or id_period_end:
            period: dict = {}
            if id_period_start:
                period["start"] = fhir_instant(id_period_start)
            if id_period_end:
                period["end"] = fhir_instant(id_period_end)
            identifier["period"] = period
        if identifier:
            entry["identifier"] = identifier

    return entry or None


def fhir_immunization_evaluation_identifier(i: ImmunizationEvaluationIdentifierModel) -> dict:
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
    if (
        assigner_id_use
        or getattr(i, "assigner_identifier_system", None)
        or getattr(i, "assigner_identifier_value", None)
    ):
        assigner_ident: dict = {}
        if assigner_id_use:
            assigner_ident["use"] = fhir_enum(assigner_id_use)
        if getattr(i, "assigner_identifier_system", None):
            assigner_ident["system"] = i.assigner_identifier_system
        if getattr(i, "assigner_identifier_value", None):
            assigner_ident["value"] = i.assigner_identifier_value
        if assigner_ident:
            assigner_entry["identifier"] = assigner_ident

    period: dict = {}
    if getattr(i, "period_start", None):
        period["start"] = fhir_instant(i.period_start)
    if getattr(i, "period_end", None):
        period["end"] = fhir_instant(i.period_end)

    type_cc = fhir_immunization_evaluation_codeable_concept(
        getattr(i, "type_codings", None), getattr(i, "type_text", None)
    )

    result = {
        "use": fhir_enum(i.use) if getattr(i, "use", None) else None,
        "type": type_cc,
        "system": i.system,
        "value": i.value,
        "period": period or None,
        "assigner": assigner_entry or None,
    }
    return {k: v for k, v in result.items() if v is not None}


def to_fhir_immunization_evaluation(m: ImmunizationEvaluationModel) -> dict:
    """Convert an ImmunizationEvaluationModel to FHIR R4 JSON representation."""
    meta = _fhir_meta(m)

    ident_list = (
        [fhir_immunization_evaluation_identifier(i) for i in m.identifiers]
        if getattr(m, "identifiers", None)
        else []
    )

    reason_list = []
    if getattr(m, "dose_status_reasons", None):
        for r in m.dose_status_reasons:
            cc = fhir_immunization_evaluation_codeable_concept(
                getattr(r, "codings", None), getattr(r, "text", None)
            )
            if cc:
                reason_list.append(cc)

    data: dict[str, Any] = {
        "resourceType": "ImmunizationEvaluation",
        "id": str(m.immunization_evaluation_id),
        "meta": meta,
        "extension": m.extension if getattr(m, "extension", None) else None,
        "identifier": ident_list or None,
        "status": fhir_enum(m.status),
        "patient": _fhir_reference_with_identifier_fallback(m, "patient"),
        "date": fhir_instant(m.date) if m.date else None,
        "authority": _fhir_reference_with_identifier_fallback(m, "authority"),
        "targetDisease": fhir_immunization_evaluation_codeable_concept(
            getattr(m, "target_disease_codings", None), m.target_disease_text
        ),
        "immunizationEvent": _fhir_reference_with_identifier_fallback(
            m, "immunization_event"
        ),
        "doseStatus": fhir_immunization_evaluation_codeable_concept(
            getattr(m, "dose_status_codings", None), m.dose_status_text
        ),
        "doseStatusReason": reason_list or None,
        "description": m.description,
        "series": m.series,
        "doseNumberPositiveInt": m.dose_number_positive_int,
        "doseNumberString": m.dose_number_string,
        "seriesDosesPositiveInt": m.series_doses_positive_int,
        "seriesDosesString": m.series_doses_string,
    }

    return {k: v for k, v in data.items() if v is not None}
