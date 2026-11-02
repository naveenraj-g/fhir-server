from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.specimen_definition import (
        SpecimenDefinitionContainerAdditive,
        SpecimenDefinitionModel,
        SpecimenDefinitionTypeTested,
        SpecimenDefinitionTypeTestedHandling,
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


def fhir_specimen_definition_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict | None:
    ref_col = "reference" if prefix == "reference" else f"{prefix}_reference"
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
    id_type_text = getattr(obj, f"{id_prefix}identifier_type_text", None)
    id_type_user_selected = getattr(obj, f"{id_prefix}identifier_type_user_selected", None)
    id_system = getattr(obj, f"{id_prefix}identifier_system", None)
    id_value = getattr(obj, f"{id_prefix}identifier_value", None)
    id_period_start = getattr(obj, f"{id_prefix}identifier_period_start", None)
    id_period_end = getattr(obj, f"{id_prefix}identifier_period_end", None)

    has_identifier = any(
        x is not None
        for x in (
            id_use,
            id_type_system,
            id_type_version,
            id_type_code,
            id_type_display,
            id_type_text,
            id_type_user_selected,
            id_system,
            id_value,
            id_period_start,
            id_period_end,
        )
    )

    if has_identifier:
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
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
            identifier["type"] = type_cc
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_period_start or id_period_end:
            p = {}
            if id_period_start:
                p["start"] = fhir_instant(id_period_start)
            if id_period_end:
                p["end"] = fhir_instant(id_period_end)
            identifier["period"] = p
        entry["identifier"] = identifier

    return entry or None


def _fhir_quantity(value, comparator=None, unit=None, system=None, code=None) -> dict | None:
    if value is None and not unit and not code:
        return None
    res: dict = {}
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


def _fhir_range(low_val, low_unit, low_sys, low_code, high_val, high_unit, high_sys, high_code) -> dict | None:
    res: dict = {}
    low = _fhir_quantity(low_val, None, low_unit, low_sys, low_code)
    if low:
        res["low"] = low
    high = _fhir_quantity(high_val, None, high_unit, high_sys, high_code)
    if high:
        res["high"] = high
    return res or None


def fhir_specimen_definition_identifier(model: SpecimenDefinitionModel) -> dict | None:
    entry: dict = {}
    if model.identifier_use:
        entry["use"] = fhir_enum(model.identifier_use)
    coding = _fhir_coding_list(model.identifier_type_codings)
    if coding or model.identifier_type_text:
        type_cc: dict = {}
        if coding:
            type_cc["coding"] = coding
        if model.identifier_type_text:
            type_cc["text"] = model.identifier_type_text
        entry["type"] = type_cc
    if model.identifier_system:
        entry["system"] = model.identifier_system
    if model.identifier_value:
        entry["value"] = model.identifier_value
    if model.identifier_period_start or model.identifier_period_end:
        p = {}
        if model.identifier_period_start:
            p["start"] = fhir_instant(model.identifier_period_start)
        if model.identifier_period_end:
            p["end"] = fhir_instant(model.identifier_period_end)
        entry["period"] = p
    assigner = _fhir_reference_with_identifier_fallback(model, "identifier_assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def fhir_specimen_definition_container_additive(a: SpecimenDefinitionContainerAdditive) -> dict | None:
    entry: dict = {}
    concept = fhir_specimen_definition_codeable_concept(a.additive_codings, a.additive_codeable_concept_text)
    if concept:
        entry["additiveCodeableConcept"] = concept
    ref = _fhir_reference_with_identifier_fallback(a, "additive_reference")
    if ref:
        entry["additiveReference"] = ref
    return entry or None


def fhir_specimen_definition_handling(h: SpecimenDefinitionTypeTestedHandling) -> dict | None:
    entry: dict = {}
    qual = fhir_specimen_definition_codeable_concept(h.temperature_qualifier_codings, h.temperature_qualifier_text)
    if qual:
        entry["temperatureQualifier"] = qual
    temp_range = _fhir_range(
        h.temperature_range_low_value,
        h.temperature_range_low_unit,
        h.temperature_range_low_system,
        h.temperature_range_low_code,
        h.temperature_range_high_value,
        h.temperature_range_high_unit,
        h.temperature_range_high_system,
        h.temperature_range_high_code,
    )
    if temp_range:
        entry["temperatureRange"] = temp_range
    dur = _fhir_quantity(
        h.max_duration_value,
        h.max_duration_comparator,
        h.max_duration_unit,
        h.max_duration_system,
        h.max_duration_code,
    )
    if dur:
        entry["maxDuration"] = dur
    if h.instruction:
        entry["instruction"] = h.instruction
    return entry or None


def fhir_specimen_definition_type_tested(tt: SpecimenDefinitionTypeTested) -> dict:
    entry: dict = {
        "preference": fhir_enum(tt.preference),
    }
    if tt.is_derived is not None:
        entry["isDerived"] = tt.is_derived
    type_cc = fhir_specimen_definition_codeable_concept(tt.type_codings, tt.type_text)
    if type_cc:
        entry["type"] = type_cc
    if tt.requirement:
        entry["requirement"] = tt.requirement

    ret_time = _fhir_quantity(
        tt.retention_time_value,
        tt.retention_time_comparator,
        tt.retention_time_unit,
        tt.retention_time_system,
        tt.retention_time_code,
    )
    if ret_time:
        entry["retentionTime"] = ret_time

    # container
    container: dict = {}
    material = fhir_specimen_definition_codeable_concept(tt.container_material_codings, tt.container_material_text)
    if material:
        container["material"] = material
    c_type = fhir_specimen_definition_codeable_concept(tt.container_type_codings, tt.container_type_text)
    if c_type:
        container["type"] = c_type
    cap = fhir_specimen_definition_codeable_concept(tt.container_cap_codings, tt.container_cap_text)
    if cap:
        container["cap"] = cap
    if tt.container_description:
        container["description"] = tt.container_description
    capacity = _fhir_quantity(
        tt.container_capacity_value,
        None,
        tt.container_capacity_unit,
        tt.container_capacity_system,
        tt.container_capacity_code,
    )
    if capacity:
        container["capacity"] = capacity
    min_vol_q = _fhir_quantity(
        tt.container_minimum_volume_quantity_value,
        None,
        tt.container_minimum_volume_quantity_unit,
        tt.container_minimum_volume_quantity_system,
        tt.container_minimum_volume_quantity_code,
    )
    if min_vol_q:
        container["minimumVolumeQuantity"] = min_vol_q
    elif tt.container_minimum_volume_string:
        container["minimumVolumeString"] = tt.container_minimum_volume_string

    additives = [
        fhir_specimen_definition_container_additive(a)
        for a in (tt.container_additives or [])
    ]
    additives = [a for a in additives if a]
    if additives:
        container["additive"] = additives
    if tt.container_preparation:
        container["preparation"] = tt.container_preparation

    if container:
        entry["container"] = container

    rejections = [
        fhir_specimen_definition_codeable_concept(rc.codings, rc.text)
        for rc in (tt.rejection_criteria or [])
    ]
    rejections = [rc for rc in rejections if rc]
    if rejections:
        entry["rejectionCriterion"] = rejections

    handlings = [
        fhir_specimen_definition_handling(h)
        for h in (tt.handlings or [])
    ]
    handlings = [h for h in handlings if h]
    if handlings:
        entry["handling"] = handlings

    return entry


def to_fhir_specimen_definition(model: SpecimenDefinitionModel) -> dict:
    """Format SpecimenDefinition ORM model as FHIR R4 JSON dict."""
    result: dict[str, Any] = {
        "resourceType": "SpecimenDefinition",
        "id": str(model.specimen_definition_id),
    }

    identifier = fhir_specimen_definition_identifier(model)
    if identifier:
        result["identifier"] = identifier

    type_collected = fhir_specimen_definition_codeable_concept(
        model.type_collected_codings, model.type_collected_text
    )
    if type_collected:
        result["typeCollected"] = type_collected

    preparations = [
        fhir_specimen_definition_codeable_concept(pp.codings, pp.text)
        for pp in (model.patient_preparations or [])
    ]
    preparations = [pp for pp in preparations if pp]
    if preparations:
        result["patientPreparation"] = preparations

    if model.time_aspect:
        result["timeAspect"] = model.time_aspect

    collections = [
        fhir_specimen_definition_codeable_concept(col.codings, col.text)
        for col in (model.collections or [])
    ]
    collections = [col for col in collections if col]
    if collections:
        result["collection"] = collections

    types_tested = [
        fhir_specimen_definition_type_tested(tt)
        for tt in (model.types_tested or [])
    ]
    if types_tested:
        result["typeTested"] = types_tested

    return {k: v for k, v in result.items() if v is not None}
