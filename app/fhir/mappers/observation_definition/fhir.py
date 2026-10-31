from typing import Any

from app.fhir.datatypes import (
    fhir_enum,
    fhir_instant,
)


def _fhir_meta(model) -> dict:
    meta: dict[str, Any] = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    elif model.created_at:
        meta["lastUpdated"] = fhir_instant(model.created_at)
    return meta


def _fhir_coding(c) -> dict | None:
    d: dict[str, Any] = {}
    if getattr(c, "system", None):
        d["system"] = c.system
    if getattr(c, "version", None):
        d["version"] = c.version
    if getattr(c, "code", None):
        d["code"] = c.code
    if getattr(c, "display", None):
        d["display"] = c.display
    if getattr(c, "user_selected", None) is not None:
        d["userSelected"] = c.user_selected
    return d or None


def _fhir_codeable_concept(codings, text: str | None) -> dict | None:
    cc: dict[str, Any] = {}
    if codings:
        cds = [_fhir_coding(c) for c in codings]
        cds = [c for c in cds if c]
        if cds:
            cc["coding"] = cds
    if text:
        cc["text"] = text
    return cc or None


def _fhir_ref(reference, ref_type, ref_id, display) -> dict | None:
    entry: dict[str, Any] = {}
    if reference:
        entry["reference"] = reference
    elif ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display
    return entry or None


def _fhir_period(start, end) -> dict | None:
    p: dict[str, Any] = {}
    if start:
        p["start"] = fhir_instant(start)
    if end:
        p["end"] = fhir_instant(end)
    return p or None


def _fhir_quantity(obj, prefix: str) -> dict | None:
    val = getattr(obj, f"{prefix}_value", None)
    unit = getattr(obj, f"{prefix}_unit", None)
    system = getattr(obj, f"{prefix}_system", None)
    code = getattr(obj, f"{prefix}_code", None)
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


def _fhir_range(obj, prefix: str) -> dict | None:
    low = _fhir_quantity(obj, f"{prefix}_low")
    high = _fhir_quantity(obj, f"{prefix}_high")
    r: dict[str, Any] = {}
    if low:
        r["low"] = low
    if high:
        r["high"] = high
    return r or None


def _fhir_identifiers(identifiers) -> list[dict]:
    result = []
    for i in identifiers:
        ident: dict[str, Any] = {}
        if i.use:
            ident["use"] = fhir_enum(i.use)
        if i.type_text or i.type_codings:
            t = _fhir_codeable_concept(i.type_codings, i.type_text)
            if t:
                ident["type"] = t
        if i.system:
            ident["system"] = i.system
        if i.value:
            ident["value"] = i.value
        p = _fhir_period(i.period_start, i.period_end)
        if p:
            ident["period"] = p
        assigner = _fhir_ref(
            i.assigner_reference, i.assigner_type, i.assigner_id, i.assigner_display
        )
        if assigner:
            ident["assigner"] = assigner
        if ident:
            result.append(ident)
    return result


def _fhir_qualified_intervals(intervals) -> list[dict]:
    result = []
    for qi in intervals:
        entry: dict[str, Any] = {}
        if qi.category:
            entry["category"] = fhir_enum(qi.category)
        r = _fhir_range(qi, "range")
        if r:
            entry["range"] = r
        ctx = _fhir_codeable_concept(qi.context_codings, qi.context_text)
        if ctx:
            entry["context"] = ctx
        if qi.applies_tos:
            applies = [
                _fhir_codeable_concept(at.codings, at.text) for at in qi.applies_tos
            ]
            applies = [a for a in applies if a]
            if applies:
                entry["appliesTo"] = applies
        if qi.gender:
            entry["gender"] = fhir_enum(qi.gender)
        age = _fhir_range(qi, "age")
        if age:
            entry["age"] = age
        ga = _fhir_range(qi, "gestational_age")
        if ga:
            entry["gestationalAge"] = ga
        if qi.condition:
            entry["condition"] = qi.condition
        if entry:
            result.append(entry)
    return result


def to_fhir_observation_definition(model) -> dict:
    """Transform an ObservationDefinitionModel into a FHIR R4 camelCase dict."""
    fhir: dict[str, Any] = {
        "resourceType": "ObservationDefinition",
        "id": str(model.observation_definition_id),
    }

    meta = _fhir_meta(model)
    if meta:
        fhir["meta"] = meta

    if model.identifiers:
        idents = _fhir_identifiers(model.identifiers)
        if idents:
            fhir["identifier"] = idents

    if model.categories:
        cats = [_fhir_codeable_concept(c.codings, c.text) for c in model.categories]
        cats = [c for c in cats if c]
        if cats:
            fhir["category"] = cats

    # code (1..1)
    code = _fhir_codeable_concept(model.code_codings, model.code_text)
    if code:
        fhir["code"] = code

    if model.permitted_data_type:
        pdt = [fhir_enum(x) for x in model.permitted_data_type]
        if pdt:
            fhir["permittedDataType"] = pdt

    if model.multiple_results_allowed is not None:
        fhir["multipleResultsAllowed"] = model.multiple_results_allowed

    if model.method_codings or model.method_text:
        method = _fhir_codeable_concept(model.method_codings, model.method_text)
        if method:
            fhir["method"] = method

    if model.preferred_report_name:
        fhir["preferredReportName"] = model.preferred_report_name

    # quantitativeDetails
    qd: dict[str, Any] = {}
    if (
        model.quantitative_details_customary_unit_codings
        or model.quantitative_details_customary_unit_text
    ):
        cu = _fhir_codeable_concept(
            model.quantitative_details_customary_unit_codings,
            model.quantitative_details_customary_unit_text,
        )
        if cu:
            qd["customaryUnit"] = cu
    if (
        model.quantitative_details_unit_codings
        or model.quantitative_details_unit_text
    ):
        u = _fhir_codeable_concept(
            model.quantitative_details_unit_codings,
            model.quantitative_details_unit_text,
        )
        if u:
            qd["unit"] = u
    if model.quantitative_details_conversion_factor is not None:
        qd["conversionFactor"] = float(model.quantitative_details_conversion_factor)
    if model.quantitative_details_decimal_precision is not None:
        qd["decimalPrecision"] = model.quantitative_details_decimal_precision
    if qd:
        fhir["quantitativeDetails"] = qd

    if model.qualified_intervals:
        qis = _fhir_qualified_intervals(model.qualified_intervals)
        if qis:
            fhir["qualifiedInterval"] = qis

    val_cs = _fhir_ref(
        model.valid_coded_value_set_reference,
        model.valid_coded_value_set_type,
        model.valid_coded_value_set_id,
        model.valid_coded_value_set_display,
    )
    if val_cs:
        fhir["validCodedValueSet"] = val_cs

    norm_cs = _fhir_ref(
        model.normal_coded_value_set_reference,
        model.normal_coded_value_set_type,
        model.normal_coded_value_set_id,
        model.normal_coded_value_set_display,
    )
    if norm_cs:
        fhir["normalCodedValueSet"] = norm_cs

    abnorm_cs = _fhir_ref(
        model.abnormal_coded_value_set_reference,
        model.abnormal_coded_value_set_type,
        model.abnormal_coded_value_set_id,
        model.abnormal_coded_value_set_display,
    )
    if abnorm_cs:
        fhir["abnormalCodedValueSet"] = abnorm_cs

    crit_cs = _fhir_ref(
        model.critical_coded_value_set_reference,
        model.critical_coded_value_set_type,
        model.critical_coded_value_set_id,
        model.critical_coded_value_set_display,
    )
    if crit_cs:
        fhir["criticalCodedValueSet"] = crit_cs

    if model.extension:
        fhir["extension"] = model.extension

    return {k: v for k, v in fhir.items() if v is not None}
