from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.immunization_evaluation.input import (
        ImmunizationEvaluationCreateSchema,
        ImmunizationEvaluationIdentifierInput,
        ImmunizationEvaluationPatchSchema,
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


def payload_immunization_evaluation_codeable_concept(cc: Any) -> dict | None:
    if cc is None:
        return None
    codings = _val(cc, "coding", None)
    coding_list = [_coding_from_payload(c) for c in codings] if codings else []
    text = _val(cc, "text", None)
    result: dict[str, Any] = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _reference_with_identifier_from_payload(ref_obj: Any) -> dict | None:
    if ref_obj is None:
        return None

    if isinstance(ref_obj, str):
        return {"reference": ref_obj}

    ref_str = _val(ref_obj, "reference", None)
    display = _val(ref_obj, "reference_display", None)

    use = _val(ref_obj, "reference_identifier_use", None)
    type_system = _val(ref_obj, "reference_identifier_type_system", None)
    type_version = _val(ref_obj, "reference_identifier_type_version", None)
    type_code = _val(ref_obj, "reference_identifier_type_code", None)
    type_display = _val(ref_obj, "reference_identifier_type_display", None)
    type_user_selected = _val(ref_obj, "reference_identifier_type_user_selected", None)
    type_text = _val(ref_obj, "reference_identifier_type_text", None)
    system = _val(ref_obj, "reference_identifier_system", None)
    value = _val(ref_obj, "reference_identifier_value", None)
    period_start = _val(ref_obj, "reference_identifier_period_start", None)
    period_end = _val(ref_obj, "reference_identifier_period_end", None)

    entry: dict[str, Any] = {}
    if ref_str:
        entry["reference"] = ref_str
    if display:
        entry["display"] = display

    if (
        use
        or type_system
        or type_version
        or type_code
        or type_display
        or type_user_selected
        or type_text
        or system
        or value
        or period_start
        or period_end
    ):
        ident: dict[str, Any] = {}
        if use:
            ident["use"] = fhir_enum(use)
        if (
            type_system
            or type_version
            or type_code
            or type_display
            or type_user_selected
            or type_text
        ):
            tc: dict[str, Any] = {}
            if type_system:
                tc["system"] = type_system
            if type_version:
                tc["version"] = type_version
            if type_code:
                tc["code"] = type_code
            if type_display:
                tc["display"] = type_display
            if type_user_selected is not None:
                tc["userSelected"] = type_user_selected
            type_cc: dict[str, Any] = {}
            if tc:
                type_cc["coding"] = [tc]
            if type_text:
                type_cc["text"] = type_text
            if type_cc:
                ident["type"] = type_cc
        if system:
            ident["system"] = system
        if value:
            ident["value"] = value
        if period_start or period_end:
            p: dict[str, Any] = {}
            if period_start:
                p["start"] = _format_datetime(period_start)
            if period_end:
                p["end"] = _format_datetime(period_end)
            ident["period"] = p
        if ident:
            entry["identifier"] = ident

    return entry or None


def payload_immunization_evaluation_identifier(
    ident: ImmunizationEvaluationIdentifierInput | dict,
) -> dict:
    if ident is None:
        return {}

    type_cc = payload_immunization_evaluation_codeable_concept(_val(ident, "type"))
    use = _val(ident, "use")
    system = _val(ident, "system")
    value = _val(ident, "value")
    start = _val(ident, "period_start")
    end = _val(ident, "period_end")

    assigner_raw = _val(ident, "assigner")
    assigner_display = _val(ident, "assigner_display")
    assigner_entry: dict[str, Any] = {}
    if assigner_raw:
        assigner_entry["reference"] = assigner_raw
    if assigner_display:
        assigner_entry["display"] = assigner_display

    assigner_id_use = _val(ident, "assigner_identifier_use")
    assigner_id_system = _val(ident, "assigner_identifier_system")
    assigner_id_value = _val(ident, "assigner_identifier_value")
    if assigner_id_use or assigner_id_system or assigner_id_value:
        assigner_ident: dict[str, Any] = {}
        if assigner_id_use:
            assigner_ident["use"] = fhir_enum(assigner_id_use)
        if assigner_id_system:
            assigner_ident["system"] = assigner_id_system
        if assigner_id_value:
            assigner_ident["value"] = assigner_id_value
        assigner_entry["identifier"] = assigner_ident

    period: dict[str, Any] = {}
    if start:
        period["start"] = _format_datetime(start)
    if end:
        period["end"] = _format_datetime(end)

    entry = {
        "use": fhir_enum(use) if use else None,
        "type": type_cc,
        "system": system,
        "value": value,
        "period": period or None,
        "assigner": assigner_entry or None,
    }
    return {k: v for k, v in entry.items() if v is not None}


def payload_to_fhir_immunization_evaluation(
    payload: ImmunizationEvaluationCreateSchema | dict,
) -> dict:
    """Convert an ImmunizationEvaluationCreateSchema to a base FHIR R4 JSON dict."""
    status = _val(payload, "status")
    patient = _reference_with_identifier_from_payload(_val(payload, "patient"))
    date_val = _val(payload, "date")
    authority = _reference_with_identifier_from_payload(_val(payload, "authority"))
    target_disease = payload_immunization_evaluation_codeable_concept(
        _val(payload, "target_disease")
    )
    immunization_event = _reference_with_identifier_from_payload(
        _val(payload, "immunization_event")
    )
    dose_status = payload_immunization_evaluation_codeable_concept(
        _val(payload, "dose_status")
    )

    reasons_in = _val(payload, "dose_status_reason") or []
    reasons = [
        payload_immunization_evaluation_codeable_concept(r) for r in reasons_in
    ]
    reasons = [r for r in reasons if r]

    idents_in = _val(payload, "identifier") or []
    identifiers = [
        payload_immunization_evaluation_identifier(i) for i in idents_in
    ]
    identifiers = [i for i in identifiers if i]

    dose_num_int = _val(payload, "dose_number_positive_int")
    dose_num_str = _val(payload, "dose_number_string")
    series_doses_int = _val(payload, "series_doses_positive_int")
    series_doses_str = _val(payload, "series_doses_string")

    data: dict[str, Any] = {
        "resourceType": "ImmunizationEvaluation",
        "identifier": identifiers or None,
        "status": fhir_enum(status),
        "patient": patient,
        "date": _format_datetime(date_val),
        "authority": authority or None,
        "targetDisease": target_disease,
        "immunizationEvent": immunization_event,
        "doseStatus": dose_status,
        "doseStatusReason": reasons or None,
        "description": _val(payload, "description"),
        "series": _val(payload, "series"),
        "doseNumberPositiveInt": dose_num_int,
        "doseNumberString": dose_num_str,
        "seriesDosesPositiveInt": series_doses_int,
        "seriesDosesString": series_doses_str,
        "extension": _val(payload, "extension"),
    }

    return {k: v for k, v in data.items() if v is not None}


def patch_fragment_to_fhir_immunization_evaluation(
    patch: ImmunizationEvaluationPatchSchema | dict,
) -> tuple[dict, set[str]]:
    """Convert an ImmunizationEvaluationPatchSchema to a partial FHIR R4 JSON dict and touched fields."""
    data = (
        patch.model_dump(exclude_unset=True)
        if hasattr(patch, "model_dump")
        else dict(patch)
    )

    fragment: dict[str, Any] = {}
    touched: set[str] = set()

    for field, val in data.items():
        if field == "status":
            touched.add("status")
            if val is not None:
                fragment["status"] = fhir_enum(val)

        elif field == "patient":
            touched.add("patient")
            if val is not None:
                fragment["patient"] = _reference_with_identifier_from_payload(val)

        elif field == "date":
            touched.add("date")
            if val is not None:
                fragment["date"] = _format_datetime(val)

        elif field == "authority":
            touched.add("authority")
            if val is not None:
                ref = _reference_with_identifier_from_payload(val)
                if ref is not None:
                    fragment["authority"] = ref

        elif field == "target_disease":
            touched.add("targetDisease")
            if val is not None:
                cc = payload_immunization_evaluation_codeable_concept(val)
                if cc is not None:
                    fragment["targetDisease"] = cc

        elif field == "immunization_event":
            touched.add("immunizationEvent")
            if val is not None:
                fragment["immunizationEvent"] = _reference_with_identifier_from_payload(val)

        elif field == "dose_status":
            touched.add("doseStatus")
            if val is not None:
                cc = payload_immunization_evaluation_codeable_concept(val)
                if cc is not None:
                    fragment["doseStatus"] = cc

        elif field == "dose_status_reason":
            touched.add("doseStatusReason")
            if val is not None:
                reasons = [
                    payload_immunization_evaluation_codeable_concept(r) for r in val
                ]
                reasons = [r for r in reasons if r]
                if reasons:
                    fragment["doseStatusReason"] = reasons

        elif field == "description":
            touched.add("description")
            if val is not None:
                fragment["description"] = val

        elif field == "series":
            touched.add("series")
            if val is not None:
                fragment["series"] = val

        elif field == "dose_number_positive_int":
            touched.add("doseNumberPositiveInt")
            touched.add("doseNumberString")
            if val is not None:
                fragment["doseNumberPositiveInt"] = val

        elif field == "dose_number_string":
            touched.add("doseNumberString")
            touched.add("doseNumberPositiveInt")
            if val is not None:
                fragment["doseNumberString"] = val

        elif field == "series_doses_positive_int":
            touched.add("seriesDosesPositiveInt")
            touched.add("seriesDosesString")
            if val is not None:
                fragment["seriesDosesPositiveInt"] = val

        elif field == "series_doses_string":
            touched.add("seriesDosesString")
            touched.add("seriesDosesPositiveInt")
            if val is not None:
                fragment["seriesDosesString"] = val

        elif field == "identifier":
            touched.add("identifier")
            if val is not None:
                idents = [payload_immunization_evaluation_identifier(i) for i in val]
                idents = [i for i in idents if i]
                if idents:
                    fragment["identifier"] = idents

        elif field == "extension":
            touched.add("extension")
            if val is not None:
                fragment["extension"] = val

    return fragment, touched
