"""Payload -> FHIR JSON conversion for MeasureReport.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(MeasureReportCreateSchema / MeasureReportPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.measure_report.input import (
        MeasureReportCreateSchema,
        MeasureReportPatchSchema,
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
    if isinstance(val, date):
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


def _codeable_concept_from_payload(codings: Any, text: str | None) -> dict | None:
    res: dict[str, Any] = {}
    if codings:
        cds = [_coding_from_payload(c) for c in codings]
        cds = [c for c in cds if c]
        if cds:
            res["coding"] = cds
    if text:
        res["text"] = text
    return res or None


def _quantity_from_payload(
    value: Any, comparator: Any, unit: Any, system: Any, code: Any
) -> dict | None:
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


def _reference_from_payload(obj: Any, prefix: str) -> dict | None:
    ref_val = _val(obj, prefix) if prefix != "reference" else _val(obj, "reference")
    if not ref_val and prefix != "reference":
        ref_val = _val(obj, f"{prefix}_reference")
    disp_val = _val(obj, f"{prefix}_display") if prefix != "reference" else _val(obj, "display")

    res: dict[str, Any] = {}
    if ref_val:
        res["reference"] = ref_val
    if disp_val:
        res["display"] = disp_val

    id_prefix = "" if prefix == "reference" else f"{prefix}_"
    id_use = _val(obj, f"{id_prefix}identifier_use")
    id_type_system = _val(obj, f"{id_prefix}identifier_type_system")
    id_type_version = _val(obj, f"{id_prefix}identifier_type_version")
    id_type_code = _val(obj, f"{id_prefix}identifier_type_code")
    id_type_display = _val(obj, f"{id_prefix}identifier_type_display")
    id_type_user_selected = _val(obj, f"{id_prefix}identifier_type_user_selected")
    id_type_text = _val(obj, f"{id_prefix}identifier_type_text")
    id_system = _val(obj, f"{id_prefix}identifier_system")
    id_value = _val(obj, f"{id_prefix}identifier_value")
    id_period_start = _val(obj, f"{id_prefix}identifier_period_start")
    id_period_end = _val(obj, f"{id_prefix}identifier_period_end")

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
        ident: dict[str, Any] = {}
        if id_use:
            ident["use"] = fhir_enum(id_use)
        if (
            id_type_system
            or id_type_code
            or id_type_display
            or id_type_text
            or id_type_version
            or id_type_user_selected is not None
        ):
            tc: dict[str, Any] = {}
            if id_type_system:
                tc["system"] = id_type_system
            if id_type_version:
                tc["version"] = id_type_version
            if id_type_code:
                tc["code"] = id_type_code
            if id_type_display:
                tc["display"] = id_type_display
            if id_type_user_selected is not None:
                tc["userSelected"] = id_type_user_selected
            type_cc: dict[str, Any] = {}
            if tc:
                type_cc["coding"] = [tc]
            if id_type_text:
                type_cc["text"] = id_type_text
            if type_cc:
                ident["type"] = type_cc
        if id_system:
            ident["system"] = id_system
        if id_value:
            ident["value"] = id_value
        if id_period_start or id_period_end:
            p_dict: dict[str, Any] = {}
            if id_period_start:
                p_dict["start"] = _format_datetime(id_period_start)
            if id_period_end:
                p_dict["end"] = _format_datetime(id_period_end)
            if p_dict:
                ident["period"] = p_dict
        res["identifier"] = ident

    return res or None


def _identifier_from_payload(ident: Any) -> dict:
    d: dict[str, Any] = {}
    use = _val(ident, "use")
    if use:
        d["use"] = fhir_enum(use)
    tc = _codeable_concept_from_payload(
        _val(ident, "type_coding"), _val(ident, "type_text")
    )
    if tc:
        d["type"] = tc
    system = _val(ident, "system")
    if system:
        d["system"] = system
    value = _val(ident, "value")
    if value:
        d["value"] = value
    p_start = _val(ident, "period_start")
    p_end = _val(ident, "period_end")
    if p_start or p_end:
        p: dict[str, Any] = {}
        if p_start:
            p["start"] = _format_datetime(p_start)
        if p_end:
            p["end"] = _format_datetime(p_end)
        if p:
            d["period"] = p
    assigner = _reference_from_payload(ident, "assigner")
    if assigner:
        d["assigner"] = assigner
    return d


def _population_from_payload(pop: Any) -> dict:
    d: dict[str, Any] = {}
    cc = _codeable_concept_from_payload(
        _val(pop, "code_coding"), _val(pop, "code_text")
    )
    if cc:
        d["code"] = cc
    count = _val(pop, "count")
    if count is not None:
        d["count"] = count
    sub_res = _reference_from_payload(pop, "subject_results")
    if sub_res:
        d["subjectResults"] = sub_res
    return d


def _component_from_payload(comp: Any) -> dict:
    d: dict[str, Any] = {}
    code_cc = _codeable_concept_from_payload(
        _val(comp, "code_coding"), _val(comp, "code_text")
    )
    if code_cc:
        d["code"] = code_cc
    val_cc = _codeable_concept_from_payload(
        _val(comp, "value_coding"), _val(comp, "value_text")
    )
    if val_cc:
        d["value"] = val_cc
    return d


def _stratum_from_payload(stratum: Any) -> dict:
    d: dict[str, Any] = {}
    val_cc = _codeable_concept_from_payload(
        _val(stratum, "value_coding"), _val(stratum, "value_text")
    )
    if val_cc:
        d["value"] = val_cc
    comps = _val(stratum, "component")
    if comps:
        d["component"] = [_component_from_payload(c) for c in comps]
    pops = _val(stratum, "population")
    if pops:
        d["population"] = [_population_from_payload(p) for p in pops]
    score = _quantity_from_payload(
        _val(stratum, "measure_score_value"),
        _val(stratum, "measure_score_comparator"),
        _val(stratum, "measure_score_unit"),
        _val(stratum, "measure_score_system"),
        _val(stratum, "measure_score_code"),
    )
    if score:
        d["measureScore"] = score
    return d


def _stratifier_from_payload(strat: Any) -> dict:
    d: dict[str, Any] = {}
    codes = _val(strat, "code")
    if codes:
        ccs = [
            _codeable_concept_from_payload(_val(c, "coding"), _val(c, "text"))
            for c in codes
        ]
        ccs = [c for c in ccs if c]
        if ccs:
            d["code"] = ccs
    strata = _val(strat, "stratum")
    if strata:
        d["stratum"] = [_stratum_from_payload(s) for s in strata]
    return d


def _group_from_payload(grp: Any) -> dict:
    d: dict[str, Any] = {}
    cc = _codeable_concept_from_payload(
        _val(grp, "code_coding"), _val(grp, "code_text")
    )
    if cc:
        d["code"] = cc
    pops = _val(grp, "population")
    if pops:
        d["population"] = [_population_from_payload(p) for p in pops]
    score = _quantity_from_payload(
        _val(grp, "measure_score_value"),
        _val(grp, "measure_score_comparator"),
        _val(grp, "measure_score_unit"),
        _val(grp, "measure_score_system"),
        _val(grp, "measure_score_code"),
    )
    if score:
        d["measureScore"] = score
    strats = _val(grp, "stratifier")
    if strats:
        d["stratifier"] = [_stratifier_from_payload(s) for s in strats]
    return d


def payload_to_fhir_measure_report(payload: MeasureReportCreateSchema) -> dict[str, Any]:
    """Convert a validated MeasureReportCreateSchema into a FHIR R4 dict for base validation."""
    fhir: dict[str, Any] = {
        "resourceType": "MeasureReport",
        "status": fhir_enum(payload.status),
        "type": fhir_enum(payload.type),
        "measure": payload.measure,
    }

    if payload.extension:
        fhir["extension"] = payload.extension

    if payload.identifier:
        fhir["identifier"] = [_identifier_from_payload(i) for i in payload.identifier]

    subject = _reference_from_payload(payload, "subject")
    if subject:
        fhir["subject"] = subject

    if payload.date:
        fhir["date"] = _format_datetime(payload.date)

    reporter = _reference_from_payload(payload, "reporter")
    if reporter:
        fhir["reporter"] = reporter

    p: dict[str, Any] = {}
    if payload.period_start:
        p["start"] = _format_datetime(payload.period_start)
    if payload.period_end:
        p["end"] = _format_datetime(payload.period_end)
    if p:
        fhir["period"] = p

    if payload.improvement_notation_coding or payload.improvement_notation_text:
        cc = _codeable_concept_from_payload(
            payload.improvement_notation_coding, payload.improvement_notation_text
        )
        if cc:
            fhir["improvementNotation"] = cc

    if payload.group:
        fhir["group"] = [_group_from_payload(g) for g in payload.group]

    if payload.evaluated_resource:
        eval_refs = [
            _reference_from_payload(er, "reference")
            for er in payload.evaluated_resource
        ]
        eval_refs = [r for r in eval_refs if r]
        if eval_refs:
            fhir["evaluatedResource"] = eval_refs

    return fhir


_SUBJECT_FIELDS = {
    "subject",
    "subject_display",
    "subject_identifier_use",
    "subject_identifier_type_system",
    "subject_identifier_type_version",
    "subject_identifier_type_code",
    "subject_identifier_type_display",
    "subject_identifier_type_user_selected",
    "subject_identifier_type_text",
    "subject_identifier_system",
    "subject_identifier_value",
    "subject_identifier_period_start",
    "subject_identifier_period_end",
}

_REPORTER_FIELDS = {
    "reporter",
    "reporter_display",
    "reporter_identifier_use",
    "reporter_identifier_type_system",
    "reporter_identifier_type_version",
    "reporter_identifier_type_code",
    "reporter_identifier_type_display",
    "reporter_identifier_type_user_selected",
    "reporter_identifier_type_text",
    "reporter_identifier_system",
    "reporter_identifier_value",
    "reporter_identifier_period_start",
    "reporter_identifier_period_end",
}

_PERIOD_FIELDS = {
    "period_start",
    "period_end",
}

_IMPROVEMENT_NOTATION_FIELDS = {
    "improvement_notation_text",
    "improvement_notation_coding",
}


def patch_fragment_to_fhir_measure_report(
    payload: MeasureReportPatchSchema,
) -> tuple[dict[str, Any], set[str]]:
    """Convert a validated MeasureReportPatchSchema into a partial FHIR fragment and touched key set."""
    provided = payload.model_fields_set
    fragment: dict[str, Any] = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        fragment["extension"] = payload.extension

    if "status" in provided:
        touched.add("status")
        fragment["status"] = fhir_enum(payload.status) if payload.status else None

    if "type" in provided:
        touched.add("type")
        fragment["type"] = fhir_enum(payload.type) if payload.type else None

    if "measure" in provided:
        touched.add("measure")
        fragment["measure"] = payload.measure

    if "date" in provided:
        touched.add("date")
        fragment["date"] = _format_datetime(payload.date) if payload.date else None

    if provided & _SUBJECT_FIELDS:
        touched.add("subject")
        fragment["subject"] = _reference_from_payload(payload, "subject")

    if provided & _REPORTER_FIELDS:
        touched.add("reporter")
        fragment["reporter"] = _reference_from_payload(payload, "reporter")

    if provided & _PERIOD_FIELDS:
        touched.add("period")
        p: dict[str, Any] = {}
        if payload.period_start:
            p["start"] = _format_datetime(payload.period_start)
        if payload.period_end:
            p["end"] = _format_datetime(payload.period_end)
        fragment["period"] = p if p else None

    if provided & _IMPROVEMENT_NOTATION_FIELDS:
        touched.add("improvementNotation")
        fragment["improvementNotation"] = _codeable_concept_from_payload(
            payload.improvement_notation_coding, payload.improvement_notation_text
        )

    if "identifier" in provided:
        touched.add("identifier")
        fragment["identifier"] = (
            [_identifier_from_payload(i) for i in payload.identifier]
            if payload.identifier is not None
            else None
        )

    if "group" in provided:
        touched.add("group")
        fragment["group"] = (
            [_group_from_payload(g) for g in payload.group]
            if payload.group is not None
            else None
        )

    if "evaluated_resource" in provided:
        touched.add("evaluatedResource")
        fragment["evaluatedResource"] = (
            [
                _reference_from_payload(er, "reference")
                for er in payload.evaluated_resource
            ]
            if payload.evaluated_resource is not None
            else None
        )

    return fragment, touched
