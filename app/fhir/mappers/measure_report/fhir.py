from typing import Any

from app.fhir.datatypes import (
    fhir_enum,
    fhir_instant,
)
from app.models.measure_report import MeasureReportModel


def _fhir_meta(model: MeasureReportModel) -> dict:
    meta: dict[str, Any] = {}
    if getattr(model, "updated_at", None):
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    elif getattr(model, "created_at", None):
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


def _fhir_quantity(value, comparator, unit, system, code) -> dict | None:
    q: dict[str, Any] = {}
    if value is not None:
        q["value"] = float(value)
    if comparator:
        q["comparator"] = fhir_enum(comparator)
    if unit:
        q["unit"] = unit
    if system:
        q["system"] = system
    if code:
        q["code"] = code
    return q or None


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
            or id_type_user_selected is not None
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
            if period:
                identifier["period"] = period
        entry["identifier"] = identifier

    return entry or None


def _fhir_identifier(ident) -> dict:
    d: dict[str, Any] = {}
    if getattr(ident, "use", None):
        d["use"] = fhir_enum(ident.use)
    if getattr(ident, "type_coding", None) or getattr(ident, "type_text", None):
        tc = _fhir_codeable_concept(
            getattr(ident, "type_coding", None), getattr(ident, "type_text", None)
        )
        if tc:
            d["type"] = tc
    if getattr(ident, "system", None):
        d["system"] = ident.system
    if getattr(ident, "value", None):
        d["value"] = ident.value
    p: dict[str, Any] = {}
    if getattr(ident, "period_start", None):
        p["start"] = fhir_instant(ident.period_start)
    if getattr(ident, "period_end", None):
        p["end"] = fhir_instant(ident.period_end)
    if p:
        d["period"] = p
    assigner = _fhir_reference_with_identifier_fallback(ident, "assigner")
    if assigner:
        d["assigner"] = assigner
    return d


def _fhir_population(pop) -> dict:
    d: dict[str, Any] = {}
    cc = _fhir_codeable_concept(getattr(pop, "code_coding", None), getattr(pop, "code_text", None))
    if cc:
        d["code"] = cc
    if getattr(pop, "count", None) is not None:
        d["count"] = pop.count
    res = _fhir_reference_with_identifier_fallback(pop, "subject_results")
    if res:
        d["subjectResults"] = res
    return d


def _fhir_component(comp) -> dict:
    d: dict[str, Any] = {}
    code_cc = _fhir_codeable_concept(
        getattr(comp, "code_coding", None), getattr(comp, "code_text", None)
    )
    if code_cc:
        d["code"] = code_cc
    val_cc = _fhir_codeable_concept(
        getattr(comp, "value_coding", None), getattr(comp, "value_text", None)
    )
    if val_cc:
        d["value"] = val_cc
    return d


def _fhir_stratum(stratum) -> dict:
    d: dict[str, Any] = {}
    val_cc = _fhir_codeable_concept(
        getattr(stratum, "value_coding", None), getattr(stratum, "value_text", None)
    )
    if val_cc:
        d["value"] = val_cc
    comps = getattr(stratum, "components", None)
    if comps:
        d["component"] = [_fhir_component(c) for c in comps]
    pops = getattr(stratum, "populations", None)
    if pops:
        d["population"] = [_fhir_population(p) for p in pops]
    score = _fhir_quantity(
        getattr(stratum, "measure_score_value", None),
        getattr(stratum, "measure_score_comparator", None),
        getattr(stratum, "measure_score_unit", None),
        getattr(stratum, "measure_score_system", None),
        getattr(stratum, "measure_score_code", None),
    )
    if score:
        d["measureScore"] = score
    return d


def _fhir_stratifier(strat) -> dict:
    d: dict[str, Any] = {}
    codes = getattr(strat, "codes", None)
    if codes:
        ccs = [
            _fhir_codeable_concept(getattr(c, "coding", None), getattr(c, "code_text", None))
            for c in codes
        ]
        ccs = [c for c in ccs if c]
        if ccs:
            d["code"] = ccs
    strata = getattr(strat, "strata", None)
    if strata:
        d["stratum"] = [_fhir_stratum(s) for s in strata]
    return d


def _fhir_group(grp) -> dict:
    d: dict[str, Any] = {}
    cc = _fhir_codeable_concept(getattr(grp, "code_coding", None), getattr(grp, "code_text", None))
    if cc:
        d["code"] = cc
    pops = getattr(grp, "populations", None)
    if pops:
        d["population"] = [_fhir_population(p) for p in pops]
    score = _fhir_quantity(
        getattr(grp, "measure_score_value", None),
        getattr(grp, "measure_score_comparator", None),
        getattr(grp, "measure_score_unit", None),
        getattr(grp, "measure_score_system", None),
        getattr(grp, "measure_score_code", None),
    )
    if score:
        d["measureScore"] = score
    strats = getattr(grp, "stratifiers", None)
    if strats:
        d["stratifier"] = [_fhir_stratifier(s) for s in strats]
    return d


def to_fhir_measure_report(model: MeasureReportModel) -> dict[str, Any]:
    """Convert MeasureReportModel ORM instance to a FHIR R4 MeasureReport resource dictionary."""
    res: dict[str, Any] = {
        "resourceType": "MeasureReport",
        "id": str(model.measure_report_id),
    }

    meta = _fhir_meta(model)
    if meta:
        res["meta"] = meta

    if model.extension:
        res["extension"] = model.extension

    if model.identifiers:
        res["identifier"] = [_fhir_identifier(i) for i in model.identifiers]

    res["status"] = fhir_enum(model.status)
    res["type"] = fhir_enum(model.type)
    res["measure"] = model.measure

    subject = _fhir_reference_with_identifier_fallback(model, "subject")
    if subject:
        res["subject"] = subject

    if model.date:
        res["date"] = fhir_instant(model.date)

    reporter = _fhir_reference_with_identifier_fallback(model, "reporter")
    if reporter:
        res["reporter"] = reporter

    p: dict[str, Any] = {}
    if model.period_start:
        p["start"] = fhir_instant(model.period_start)
    if model.period_end:
        p["end"] = fhir_instant(model.period_end)
    if p:
        res["period"] = p

    if model.improvement_notation_coding or model.improvement_notation_text:
        cc = _fhir_codeable_concept(
            model.improvement_notation_coding, model.improvement_notation_text
        )
        if cc:
            res["improvementNotation"] = cc

    if model.groups:
        res["group"] = [_fhir_group(g) for g in model.groups]

    if model.evaluated_resources:
        eval_refs = [
            _fhir_reference_with_identifier_fallback(er, "evaluated_resource")
            for er in model.evaluated_resources
        ]
        eval_refs = [r for r in eval_refs if r]
        if eval_refs:
            res["evaluatedResource"] = eval_refs

    return {k: v for k, v in res.items() if v is not None}
