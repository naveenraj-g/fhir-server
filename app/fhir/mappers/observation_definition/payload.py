"""Payload -> FHIR JSON conversion for ObservationDefinition.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(ObservationDefinitionCreateSchema / ObservationDefinitionPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.observation_definition.input import (
        ObservationDefinitionCodeableConceptInput,
        ObservationDefinitionCreateSchema,
        ObservationDefinitionIdentifierInput,
        ObservationDefinitionPatchSchema,
        ObservationDefinitionQualifiedIntervalInput,
        ObservationDefinitionQuantitativeDetailsInput,
    )


def _coding_from_payload(c) -> dict:
    if isinstance(c, dict):
        return {
            k: v
            for k, v in {
                "system": c.get("system"),
                "version": c.get("version"),
                "code": c.get("code"),
                "display": c.get("display"),
                "userSelected": c.get("user_selected") or c.get("userSelected"),
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


def _codeable_concept_from_payload(
    concept: ObservationDefinitionCodeableConceptInput | None,
) -> dict | None:
    if not concept:
        return None
    codings = [_coding_from_payload(c) for c in (concept.coding or [])]
    codings = [c for c in codings if c]
    result: dict = {}
    if codings:
        result["coding"] = codings
    if concept.text:
        result["text"] = concept.text
    return result or None


def _identifier_from_payload(i: ObservationDefinitionIdentifierInput) -> dict:
    ident: dict[str, Any] = {}
    if i.use:
        ident["use"] = fhir_enum(i.use)
    if i.system:
        ident["system"] = i.system
    if i.value:
        ident["value"] = i.value

    if i.type:
        t = _codeable_concept_from_payload(i.type)
        if t:
            ident["type"] = t

    period: dict[str, Any] = {}
    if i.period_start:
        period["start"] = i.period_start.isoformat()
    if i.period_end:
        period["end"] = i.period_end.isoformat()
    if period:
        ident["period"] = period

    if i.assigner:
        assigner: dict[str, Any] = {"reference": i.assigner}
        if i.assigner_display:
            assigner["display"] = i.assigner_display
        ident["assigner"] = assigner

    return ident


def _quantity_from_payload(val, unit, system, code) -> dict | None:
    q: dict[str, Any] = {}
    if val is not None:
        q["value"] = float(val)
    if unit:
        q["unit"] = unit
    if system:
        q["system"] = system
    if code:
        q["code"] = code
    return q or None


def _range_from_payload(low_val, low_unit, low_sys, low_code, high_val, high_unit, high_sys, high_code) -> dict | None:
    low = _quantity_from_payload(low_val, low_unit, low_sys, low_code)
    high = _quantity_from_payload(high_val, high_unit, high_sys, high_code)
    r: dict[str, Any] = {}
    if low:
        r["low"] = low
    if high:
        r["high"] = high
    return r or None


def _quantitative_details_from_payload(
    qd: ObservationDefinitionQuantitativeDetailsInput | None,
) -> dict | None:
    if not qd:
        return None
    res: dict[str, Any] = {}
    if qd.customary_unit:
        cu = _codeable_concept_from_payload(qd.customary_unit)
        if cu:
            res["customaryUnit"] = cu
    if qd.unit:
        u = _codeable_concept_from_payload(qd.unit)
        if u:
            res["unit"] = u
    if qd.conversion_factor is not None:
        res["conversionFactor"] = float(qd.conversion_factor)
    if qd.decimal_precision is not None:
        res["decimalPrecision"] = qd.decimal_precision
    return res or None


def _qualified_interval_from_payload(
    qi: ObservationDefinitionQualifiedIntervalInput,
) -> dict | None:
    res: dict[str, Any] = {}
    if qi.category:
        res["category"] = fhir_enum(qi.category)
    r = _range_from_payload(
        qi.range_low_value, qi.range_low_unit, qi.range_low_system, qi.range_low_code,
        qi.range_high_value, qi.range_high_unit, qi.range_high_system, qi.range_high_code,
    )
    if r:
        res["range"] = r
    if qi.context:
        ctx = _codeable_concept_from_payload(qi.context)
        if ctx:
            res["context"] = ctx
    if qi.applies_to:
        applies = [_codeable_concept_from_payload(at) for at in qi.applies_to]
        applies = [a for a in applies if a]
        if applies:
            res["appliesTo"] = applies
    if qi.gender:
        res["gender"] = fhir_enum(qi.gender)
    age = _range_from_payload(
        qi.age_low_value, qi.age_low_unit, qi.age_low_system, qi.age_low_code,
        qi.age_high_value, qi.age_high_unit, qi.age_high_system, qi.age_high_code,
    )
    if age:
        res["age"] = age
    ga = _range_from_payload(
        qi.gestational_age_low_value, qi.gestational_age_low_unit, qi.gestational_age_low_system, qi.gestational_age_low_code,
        qi.gestational_age_high_value, qi.gestational_age_high_unit, qi.gestational_age_high_system, qi.gestational_age_high_code,
    )
    if ga:
        res["gestationalAge"] = ga
    if qi.condition:
        res["condition"] = qi.condition
    return res or None


def payload_to_fhir_observation_definition(
    payload: ObservationDefinitionCreateSchema,
) -> dict[str, Any]:
    """Convert an ObservationDefinitionCreateSchema to a FHIR R4 dict for pre-write validation."""
    fhir: dict[str, Any] = {
        "resourceType": "ObservationDefinition",
    }

    if payload.code:
        code = _codeable_concept_from_payload(payload.code)
        if code:
            fhir["code"] = code

    if payload.category:
        cats = [_codeable_concept_from_payload(c) for c in payload.category]
        cats = [c for c in cats if c]
        if cats:
            fhir["category"] = cats

    if payload.identifier:
        idents = [_identifier_from_payload(i) for i in payload.identifier]
        idents = [i for i in idents if i]
        if idents:
            fhir["identifier"] = idents

    if payload.permitted_data_type:
        fhir["permittedDataType"] = [fhir_enum(x) for x in payload.permitted_data_type]

    if payload.multiple_results_allowed is not None:
        fhir["multipleResultsAllowed"] = payload.multiple_results_allowed

    if payload.method:
        method = _codeable_concept_from_payload(payload.method)
        if method:
            fhir["method"] = method

    if payload.preferred_report_name:
        fhir["preferredReportName"] = payload.preferred_report_name

    if payload.quantitative_details:
        qd = _quantitative_details_from_payload(payload.quantitative_details)
        if qd:
            fhir["quantitativeDetails"] = qd

    if payload.qualified_interval:
        qis = [_qualified_interval_from_payload(qi) for qi in payload.qualified_interval]
        qis = [qi for qi in qis if qi]
        if qis:
            fhir["qualifiedInterval"] = qis

    if payload.valid_coded_value_set:
        ref: dict[str, Any] = {"reference": payload.valid_coded_value_set}
        if payload.valid_coded_value_set_display:
            ref["display"] = payload.valid_coded_value_set_display
        fhir["validCodedValueSet"] = ref

    if payload.normal_coded_value_set:
        ref = {"reference": payload.normal_coded_value_set}
        if payload.normal_coded_value_set_display:
            ref["display"] = payload.normal_coded_value_set_display
        fhir["normalCodedValueSet"] = ref

    if payload.abnormal_coded_value_set:
        ref = {"reference": payload.abnormal_coded_value_set}
        if payload.abnormal_coded_value_set_display:
            ref["display"] = payload.abnormal_coded_value_set_display
        fhir["abnormalCodedValueSet"] = ref

    if payload.critical_coded_value_set:
        ref = {"reference": payload.critical_coded_value_set}
        if payload.critical_coded_value_set_display:
            ref["display"] = payload.critical_coded_value_set_display
        fhir["criticalCodedValueSet"] = ref

    if payload.extension:
        fhir["extension"] = payload.extension

    return fhir


def patch_fragment_to_fhir_observation_definition(
    payload: ObservationDefinitionPatchSchema,
) -> tuple[dict, set[str]]:
    """Map touched fields of ObservationDefinitionPatchSchema to a partial FHIR dict and set of touched keys."""
    touched: set[str] = set()
    fragment: dict = {}
    fields_set = payload.model_fields_set

    if "code" in fields_set:
        touched.add("code")
        if payload.code is not None:
            c = _codeable_concept_from_payload(payload.code)
            if c:
                fragment["code"] = c

    if "category" in fields_set:
        touched.add("category")
        if payload.category is not None:
            fragment["category"] = [
                c for c in [_codeable_concept_from_payload(x) for x in payload.category] if c
            ]

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                i for i in [_identifier_from_payload(x) for x in payload.identifier] if i
            ]

    if "permitted_data_type" in fields_set:
        touched.add("permittedDataType")
        if payload.permitted_data_type is not None:
            fragment["permittedDataType"] = [
                fhir_enum(x) for x in payload.permitted_data_type
            ]

    if "multiple_results_allowed" in fields_set:
        touched.add("multipleResultsAllowed")
        if payload.multiple_results_allowed is not None:
            fragment["multipleResultsAllowed"] = payload.multiple_results_allowed

    if "method" in fields_set:
        touched.add("method")
        if payload.method is not None:
            m = _codeable_concept_from_payload(payload.method)
            if m:
                fragment["method"] = m

    if "preferred_report_name" in fields_set:
        touched.add("preferredReportName")
        if payload.preferred_report_name is not None:
            fragment["preferredReportName"] = payload.preferred_report_name

    if "quantitative_details" in fields_set:
        touched.add("quantitativeDetails")
        if payload.quantitative_details is not None:
            qd = _quantitative_details_from_payload(payload.quantitative_details)
            if qd:
                fragment["quantitativeDetails"] = qd

    if "qualified_interval" in fields_set:
        touched.add("qualifiedInterval")
        if payload.qualified_interval is not None:
            fragment["qualifiedInterval"] = [
                qi for qi in [_qualified_interval_from_payload(x) for x in payload.qualified_interval] if qi
            ]

    if "valid_coded_value_set" in fields_set or "valid_coded_value_set_display" in fields_set:
        touched.add("validCodedValueSet")
        if payload.valid_coded_value_set is not None:
            ref: dict[str, Any] = {"reference": payload.valid_coded_value_set}
            if payload.valid_coded_value_set_display:
                ref["display"] = payload.valid_coded_value_set_display
            fragment["validCodedValueSet"] = ref

    if "normal_coded_value_set" in fields_set or "normal_coded_value_set_display" in fields_set:
        touched.add("normalCodedValueSet")
        if payload.normal_coded_value_set is not None:
            ref = {"reference": payload.normal_coded_value_set}
            if payload.normal_coded_value_set_display:
                ref["display"] = payload.normal_coded_value_set_display
            fragment["normalCodedValueSet"] = ref

    if "abnormal_coded_value_set" in fields_set or "abnormal_coded_value_set_display" in fields_set:
        touched.add("abnormalCodedValueSet")
        if payload.abnormal_coded_value_set is not None:
            ref = {"reference": payload.abnormal_coded_value_set}
            if payload.abnormal_coded_value_set_display:
                ref["display"] = payload.abnormal_coded_value_set_display
            fragment["abnormalCodedValueSet"] = ref

    if "critical_coded_value_set" in fields_set or "critical_coded_value_set_display" in fields_set:
        touched.add("criticalCodedValueSet")
        if payload.critical_coded_value_set is not None:
            ref = {"reference": payload.critical_coded_value_set}
            if payload.critical_coded_value_set_display:
                ref["display"] = payload.critical_coded_value_set_display
            fragment["criticalCodedValueSet"] = ref

    if "extension" in fields_set:
        touched.add("extension")
        if payload.extension is not None:
            fragment["extension"] = payload.extension

    return fragment, touched
