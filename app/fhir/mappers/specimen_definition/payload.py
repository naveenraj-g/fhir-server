"""Payload -> FHIR JSON conversion for SpecimenDefinition.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(SpecimenDefinitionCreateSchema / SpecimenDefinitionPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.specimen_definition.input import (
        SpecimenDefinitionCreateSchema,
        SpecimenDefinitionPatchSchema,
    )

_COMPARATOR_MAP = {
    "lt": "<",
    "le": "<=",
    "ge": ">=",
    "gt": ">",
    "<": "<",
    "<=": "<=",
    ">=": ">=",
    ">": ">",
}


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


def payload_specimen_definition_codeable_concept(cc: Any) -> dict | None:
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
    res: dict[str, Any] = {}
    raw_ref = _val(ref_obj, "reference", None)
    if raw_ref:
        res["reference"] = raw_ref
    display = _val(ref_obj, "display", None)
    if display:
        res["display"] = display

    id_use = _val(ref_obj, "identifier_use", None)
    id_sys = _val(ref_obj, "identifier_system", None)
    id_val = _val(ref_obj, "identifier_value", None)
    id_p_start = _val(ref_obj, "identifier_period_start", None)
    id_p_end = _val(ref_obj, "identifier_period_end", None)

    id_type_system = _val(ref_obj, "identifier_type_system", None)
    id_type_version = _val(ref_obj, "identifier_type_version", None)
    id_type_code = _val(ref_obj, "identifier_type_code", None)
    id_type_display = _val(ref_obj, "identifier_type_display", None)
    id_type_user_selected = _val(ref_obj, "identifier_type_user_selected", None)
    id_type_text = _val(ref_obj, "identifier_type_text", None)

    has_id = any(
        x is not None
        for x in (
            id_use,
            id_sys,
            id_val,
            id_p_start,
            id_p_end,
            id_type_system,
            id_type_version,
            id_type_code,
            id_type_display,
            id_type_user_selected,
            id_type_text,
        )
    )

    if has_id:
        ident: dict[str, Any] = {}
        if id_use:
            ident["use"] = fhir_enum(id_use)
        if id_sys:
            ident["system"] = id_sys
        if id_val:
            ident["value"] = id_val
        type_codings = []
        if any(x is not None for x in (id_type_system, id_type_version, id_type_code, id_type_display, id_type_user_selected)):
            tc = {}
            if id_type_system is not None:
                tc["system"] = id_type_system
            if id_type_version is not None:
                tc["version"] = id_type_version
            if id_type_code is not None:
                tc["code"] = id_type_code
            if id_type_display is not None:
                tc["display"] = id_type_display
            if id_type_user_selected is not None:
                tc["userSelected"] = id_type_user_selected
            if tc:
                type_codings.append(tc)
        if type_codings or id_type_text:
            type_cc: dict = {}
            if type_codings:
                type_cc["coding"] = type_codings
            if id_type_text:
                type_cc["text"] = id_type_text
            ident["type"] = type_cc
        if id_p_start or id_p_end:
            p = {}
            if id_p_start:
                p["start"] = _format_datetime(id_p_start)
            if id_p_end:
                p["end"] = _format_datetime(id_p_end)
            ident["period"] = p
        res["identifier"] = ident

    return res or None


def _payload_quantity(value, comparator=None, unit=None, system=None, code=None) -> dict | None:
    if value is None and not unit and not code:
        return None
    res: dict[str, Any] = {}
    if value is not None:
        res["value"] = float(value)
    if comparator:
        comp_str = fhir_enum(comparator)
        res["comparator"] = _COMPARATOR_MAP.get(comp_str, comp_str)
    if unit:
        res["unit"] = unit
    if system:
        res["system"] = system
    if code:
        res["code"] = code
    return res or None


def _payload_range(low_val, low_unit, low_sys, low_code, high_val, high_unit, high_sys, high_code) -> dict | None:
    res: dict[str, Any] = {}
    low = _payload_quantity(low_val, None, low_unit, low_sys, low_code)
    if low:
        res["low"] = low
    high = _payload_quantity(high_val, None, high_unit, high_sys, high_code)
    if high:
        res["high"] = high
    return res or None


def payload_specimen_definition_identifier(ident: Any) -> dict | None:
    if ident is None:
        return None
    res: dict[str, Any] = {}
    use = _val(ident, "use", None)
    if use:
        res["use"] = fhir_enum(use)
    sys = _val(ident, "system", None)
    if sys:
        res["system"] = sys
    val = _val(ident, "value", None)
    if val:
        res["value"] = val
    type_codings = _val(ident, "type_coding", None)
    type_text = _val(ident, "type_text", None)
    codings = [_coding_from_payload(c) for c in type_codings] if type_codings else []
    if codings or type_text:
        type_cc: dict = {}
        if codings:
            type_cc["coding"] = codings
        if type_text:
            type_cc["text"] = type_text
        res["type"] = type_cc
    p_start = _val(ident, "period_start", None)
    p_end = _val(ident, "period_end", None)
    if p_start or p_end:
        p = {}
        if p_start:
            p["start"] = _format_datetime(p_start)
        if p_end:
            p["end"] = _format_datetime(p_end)
        res["period"] = p

    assigner = _val(ident, "assigner", None)
    assigner_display = _val(ident, "assigner_display", None)
    if assigner or assigner_display:
        ass_dict: dict = {}
        if assigner:
            ass_dict["reference"] = assigner
        if assigner_display:
            ass_dict["display"] = assigner_display
        res["assigner"] = ass_dict

    return res or None


def payload_specimen_definition_container_additive(a: Any) -> dict | None:
    if a is None:
        return None
    res: dict[str, Any] = {}
    concept = payload_specimen_definition_codeable_concept(_val(a, "additive_codeable_concept", None))
    if concept:
        res["additiveCodeableConcept"] = concept
    ref = _reference_with_identifier_from_payload(_val(a, "additive_reference", None))
    if ref:
        res["additiveReference"] = ref
    return res or None


def payload_specimen_definition_handling(h: Any) -> dict | None:
    if h is None:
        return None
    res: dict[str, Any] = {}
    qual = payload_specimen_definition_codeable_concept(_val(h, "temperature_qualifier", None))
    if qual:
        res["temperatureQualifier"] = qual
    temp_range = _payload_range(
        _val(h, "temperature_range_low_value", None),
        _val(h, "temperature_range_low_unit", None),
        _val(h, "temperature_range_low_system", None),
        _val(h, "temperature_range_low_code", None),
        _val(h, "temperature_range_high_value", None),
        _val(h, "temperature_range_high_unit", None),
        _val(h, "temperature_range_high_system", None),
        _val(h, "temperature_range_high_code", None),
    )
    if temp_range:
        res["temperatureRange"] = temp_range
    dur = _payload_quantity(
        _val(h, "max_duration_value", None),
        _val(h, "max_duration_comparator", None),
        _val(h, "max_duration_unit", None),
        _val(h, "max_duration_system", None),
        _val(h, "max_duration_code", None),
    )
    if dur:
        res["maxDuration"] = dur
    inst = _val(h, "instruction", None)
    if inst:
        res["instruction"] = inst
    return res or None


def payload_specimen_definition_container(c: Any) -> dict | None:
    if c is None:
        return None
    res: dict[str, Any] = {}
    mat = payload_specimen_definition_codeable_concept(_val(c, "material", None))
    if mat:
        res["material"] = mat
    c_type = payload_specimen_definition_codeable_concept(_val(c, "type", None))
    if c_type:
        res["type"] = c_type
    cap = payload_specimen_definition_codeable_concept(_val(c, "cap", None))
    if cap:
        res["cap"] = cap
    desc = _val(c, "description", None)
    if desc:
        res["description"] = desc
    capacity = _payload_quantity(
        _val(c, "capacity_value", None),
        None,
        _val(c, "capacity_unit", None),
        _val(c, "capacity_system", None),
        _val(c, "capacity_code", None),
    )
    if capacity:
        res["capacity"] = capacity
    min_vol_q = _payload_quantity(
        _val(c, "minimum_volume_quantity_value", None),
        None,
        _val(c, "minimum_volume_quantity_unit", None),
        _val(c, "minimum_volume_quantity_system", None),
        _val(c, "minimum_volume_quantity_code", None),
    )
    if min_vol_q:
        res["minimumVolumeQuantity"] = min_vol_q
    else:
        min_vol_s = _val(c, "minimum_volume_string", None)
        if min_vol_s:
            res["minimumVolumeString"] = min_vol_s

    additives = _val(c, "additive", None)
    if additives:
        ad_list = [payload_specimen_definition_container_additive(a) for a in additives]
        ad_list = [a for a in ad_list if a]
        if ad_list:
            res["additive"] = ad_list
    prep = _val(c, "preparation", None)
    if prep:
        res["preparation"] = prep

    return res or None


def payload_specimen_definition_type_tested(tt: Any) -> dict:
    pref = _val(tt, "preference", None)
    res: dict[str, Any] = {
        "preference": fhir_enum(pref) if pref else "preferred",
    }
    is_der = _val(tt, "is_derived", None)
    if is_der is not None:
        res["isDerived"] = is_der
    type_cc = payload_specimen_definition_codeable_concept(_val(tt, "type", None))
    if type_cc:
        res["type"] = type_cc
    req = _val(tt, "requirement", None)
    if req:
        res["requirement"] = req
    ret_time = _payload_quantity(
        _val(tt, "retention_time_value", None),
        _val(tt, "retention_time_comparator", None),
        _val(tt, "retention_time_unit", None),
        _val(tt, "retention_time_system", None),
        _val(tt, "retention_time_code", None),
    )
    if ret_time:
        res["retentionTime"] = ret_time

    container = payload_specimen_definition_container(_val(tt, "container", None))
    if container:
        res["container"] = container

    rejections = _val(tt, "rejection_criterion", None)
    if rejections:
        rej_list = [payload_specimen_definition_codeable_concept(rc) for rc in rejections]
        rej_list = [rc for rc in rej_list if rc]
        if rej_list:
            res["rejectionCriterion"] = rej_list

    handlings = _val(tt, "handling", None)
    if handlings:
        h_list = [payload_specimen_definition_handling(h) for h in handlings]
        h_list = [h for h in h_list if h]
        if h_list:
            res["handling"] = h_list

    return res


def payload_to_fhir_specimen_definition(
    payload: SpecimenDefinitionCreateSchema | dict[str, Any],
) -> dict[str, Any]:
    """Convert a CREATE payload to full FHIR R4 SpecimenDefinition JSON."""
    result: dict[str, Any] = {
        "resourceType": "SpecimenDefinition",
        "id": "placeholder",
    }

    ident = payload_specimen_definition_identifier(_val(payload, "identifier", None))
    if ident:
        result["identifier"] = ident

    type_coll = payload_specimen_definition_codeable_concept(_val(payload, "type_collected", None))
    if type_coll:
        result["typeCollected"] = type_coll

    preps = _val(payload, "patient_preparation", None)
    if preps:
        prep_list = [payload_specimen_definition_codeable_concept(p) for p in preps]
        prep_list = [p for p in prep_list if p]
        if prep_list:
            result["patientPreparation"] = prep_list

    time_asp = _val(payload, "time_aspect", None)
    if time_asp:
        result["timeAspect"] = time_asp

    colls = _val(payload, "collection", None)
    if colls:
        coll_list = [payload_specimen_definition_codeable_concept(c) for c in colls]
        coll_list = [c for c in coll_list if c]
        if coll_list:
            result["collection"] = coll_list

    types_tested = _val(payload, "type_tested", None)
    if types_tested:
        tt_list = [payload_specimen_definition_type_tested(tt) for tt in types_tested]
        if tt_list:
            result["typeTested"] = tt_list

    return result


def patch_fragment_to_fhir_specimen_definition(
    payload: SpecimenDefinitionPatchSchema | dict[str, Any],
) -> tuple[dict[str, Any], set[str]]:
    """Convert a PATCH fragment to partial FHIR dict + touched FHIR top-level keys."""
    provided: set[str] = (
        payload.model_fields_set
        if hasattr(payload, "model_fields_set")
        else set(payload.keys())
    )
    fragment: dict[str, Any] = {}
    touched: set[str] = set()

    if "identifier" in provided:
        touched.add("identifier")
        ident = _val(payload, "identifier", None)
        fragment["identifier"] = (
            payload_specimen_definition_identifier(ident)
            if ident is not None
            else None
        )

    if "type_collected" in provided:
        touched.add("typeCollected")
        tc = _val(payload, "type_collected", None)
        fragment["typeCollected"] = (
            payload_specimen_definition_codeable_concept(tc)
            if tc is not None
            else None
        )

    if "patient_preparation" in provided:
        touched.add("patientPreparation")
        preps = _val(payload, "patient_preparation", None)
        fragment["patientPreparation"] = (
            [
                payload_specimen_definition_codeable_concept(p)
                for p in preps
                if p
            ]
            if preps is not None
            else None
        )

    if "time_aspect" in provided:
        touched.add("timeAspect")
        fragment["timeAspect"] = _val(payload, "time_aspect", None)

    if "collection" in provided:
        touched.add("collection")
        colls = _val(payload, "collection", None)
        fragment["collection"] = (
            [
                payload_specimen_definition_codeable_concept(c)
                for c in colls
                if c
            ]
            if colls is not None
            else None
        )

    if "type_tested" in provided:
        touched.add("typeTested")
        tts = _val(payload, "type_tested", None)
        fragment["typeTested"] = (
            [
                payload_specimen_definition_type_tested(tt)
                for tt in tts
                if tt
            ]
            if tts is not None
            else None
        )

    return fragment, touched
