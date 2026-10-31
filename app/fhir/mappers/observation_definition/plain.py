from typing import Any

from app.fhir.datatypes import fhir_enum


def _plain_coding(c) -> dict:
    return {
        "system": getattr(c, "system", None),
        "version": getattr(c, "version", None),
        "code": getattr(c, "code", None),
        "display": getattr(c, "display", None),
        "user_selected": getattr(c, "user_selected", None),
    }


def _plain_codings(codings) -> list[dict]:
    if not codings:
        return []
    return [_plain_coding(c) for c in codings]


def _plain_codeable_concept(codings, text: str | None) -> dict | None:
    if not codings and not text:
        return None
    return {
        "text": text,
        "codings": _plain_codings(codings),
    }


def _plain_identifiers(identifiers) -> list[dict]:
    result = []
    for i in identifiers:
        ref_str = i.assigner_reference
        if not ref_str and i.assigner_type and i.assigner_id:
            ref_str = f"{fhir_enum(i.assigner_type)}/{i.assigner_id}"
        result.append(
            {
                "id": i.id,
                "use": fhir_enum(i.use) if i.use else None,
                "system": i.system,
                "value": i.value,
                "type_text": i.type_text,
                "type_codings": _plain_codings(i.type_codings),
                "period_start": i.period_start,
                "period_end": i.period_end,
                "assigner": ref_str,
                "assigner_display": i.assigner_display,
            }
        )
    return result


def _plain_qualified_intervals(intervals) -> list[dict]:
    result = []
    for qi in intervals:
        applies_to_list = []
        if qi.applies_tos:
            for at in qi.applies_tos:
                applies_to_list.append(
                    {
                        "id": at.id,
                        "text": at.text,
                        "codings": _plain_codings(at.codings),
                    }
                )

        result.append(
            {
                "id": qi.id,
                "category": fhir_enum(qi.category) if qi.category else None,
                "range_low_value": float(qi.range_low_value) if qi.range_low_value is not None else None,
                "range_low_unit": qi.range_low_unit,
                "range_low_system": qi.range_low_system,
                "range_low_code": qi.range_low_code,
                "range_high_value": float(qi.range_high_value) if qi.range_high_value is not None else None,
                "range_high_unit": qi.range_high_unit,
                "range_high_system": qi.range_high_system,
                "range_high_code": qi.range_high_code,
                "context_text": qi.context_text,
                "context_codings": _plain_codings(qi.context_codings),
                "applies_to": applies_to_list,
                "gender": fhir_enum(qi.gender) if qi.gender else None,
                "age_low_value": float(qi.age_low_value) if qi.age_low_value is not None else None,
                "age_low_unit": qi.age_low_unit,
                "age_low_system": qi.age_low_system,
                "age_low_code": qi.age_low_code,
                "age_high_value": float(qi.age_high_value) if qi.age_high_value is not None else None,
                "age_high_unit": qi.age_high_unit,
                "age_high_system": qi.age_high_system,
                "age_high_code": qi.age_high_code,
                "gestational_age_low_value": float(qi.gestational_age_low_value) if qi.gestational_age_low_value is not None else None,
                "gestational_age_low_unit": qi.gestational_age_low_unit,
                "gestational_age_low_system": qi.gestational_age_low_system,
                "gestational_age_low_code": qi.gestational_age_low_code,
                "gestational_age_high_value": float(qi.gestational_age_high_value) if qi.gestational_age_high_value is not None else None,
                "gestational_age_high_unit": qi.gestational_age_high_unit,
                "gestational_age_high_system": qi.gestational_age_high_system,
                "gestational_age_high_code": qi.gestational_age_high_code,
                "condition": qi.condition,
            }
        )
    return result


def to_plain_observation_definition(model) -> dict:
    """Transform an ObservationDefinitionModel into a plain snake_case dict."""
    categories_list = []
    if model.categories:
        for c in model.categories:
            categories_list.append(
                {
                    "id": c.id,
                    "text": c.text,
                    "codings": _plain_codings(c.codings),
                }
            )

    qd_dict = None
    if (
        model.quantitative_details_customary_unit_text
        or model.quantitative_details_customary_unit_codings
        or model.quantitative_details_unit_text
        or model.quantitative_details_unit_codings
        or model.quantitative_details_conversion_factor is not None
        or model.quantitative_details_decimal_precision is not None
    ):
        qd_dict = {
            "customary_unit_text": model.quantitative_details_customary_unit_text,
            "customary_unit_codings": _plain_codings(
                model.quantitative_details_customary_unit_codings
            ),
            "unit_text": model.quantitative_details_unit_text,
            "unit_codings": _plain_codings(model.quantitative_details_unit_codings),
            "conversion_factor": (
                float(model.quantitative_details_conversion_factor)
                if model.quantitative_details_conversion_factor is not None
                else None
            ),
            "decimal_precision": model.quantitative_details_decimal_precision,
        }

    val_cs = model.valid_coded_value_set_reference
    if not val_cs and model.valid_coded_value_set_type and model.valid_coded_value_set_id:
        val_cs = f"{fhir_enum(model.valid_coded_value_set_type)}/{model.valid_coded_value_set_id}"

    norm_cs = model.normal_coded_value_set_reference
    if not norm_cs and model.normal_coded_value_set_type and model.normal_coded_value_set_id:
        norm_cs = f"{fhir_enum(model.normal_coded_value_set_type)}/{model.normal_coded_value_set_id}"

    abnorm_cs = model.abnormal_coded_value_set_reference
    if not abnorm_cs and model.abnormal_coded_value_set_type and model.abnormal_coded_value_set_id:
        abnorm_cs = f"{fhir_enum(model.abnormal_coded_value_set_type)}/{model.abnormal_coded_value_set_id}"

    crit_cs = model.critical_coded_value_set_reference
    if not crit_cs and model.critical_coded_value_set_type and model.critical_coded_value_set_id:
        crit_cs = f"{fhir_enum(model.critical_coded_value_set_type)}/{model.critical_coded_value_set_id}"

    return {
        "id": model.observation_definition_id,
        "tenant_id": model.tenant_id,
        "code": _plain_codeable_concept(model.code_codings, model.code_text),
        "category": categories_list,
        "identifier": _plain_identifiers(model.identifiers) if model.identifiers else [],
        "permitted_data_type": (
            [fhir_enum(x) for x in model.permitted_data_type]
            if model.permitted_data_type
            else []
        ),
        "multiple_results_allowed": model.multiple_results_allowed,
        "method": _plain_codeable_concept(model.method_codings, model.method_text),
        "preferred_report_name": model.preferred_report_name,
        "quantitative_details": qd_dict,
        "qualified_interval": (
            _plain_qualified_intervals(model.qualified_intervals)
            if model.qualified_intervals
            else []
        ),
        "valid_coded_value_set": val_cs,
        "valid_coded_value_set_display": model.valid_coded_value_set_display,
        "normal_coded_value_set": norm_cs,
        "normal_coded_value_set_display": model.normal_coded_value_set_display,
        "abnormal_coded_value_set": abnorm_cs,
        "abnormal_coded_value_set_display": model.abnormal_coded_value_set_display,
        "critical_coded_value_set": crit_cs,
        "critical_coded_value_set_display": model.critical_coded_value_set_display,
        "extension": model.extension or [],
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
