"""Payload -> FHIR JSON conversion, the mirror image of fhir.py — see that
module's docstring pattern (e.g. app.fhir.mappers.medication_request.payload)
for the full reasoning. Reads the validated Pydantic input schema
(ObservationCreateSchema / ObservationPatchSchema and their nested
sub-schemas) rather than the persisted ORM model, before anything is
written to the DB.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.observation.input import (
        ObservationCreateSchema,
        ObservationIdentifierInput,
        ObservationNoteInput,
        ObservationPatchSchema,
    )
    from app.schemas.observation.input.codeable_concept import ObservationCodeableConceptInput
    from app.schemas.observation.input.component import ObservationComponentInput
    from app.schemas.observation.input.reference_range import ObservationReferenceRangeInput


def _coding_list(codings) -> list[dict]:
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


def _period(start, end) -> dict | None:
    period = {
        k: v
        for k, v in {"start": start.isoformat() if start else None, "end": end.isoformat() if end else None}.items()
        if v
    }
    return period or None


def _reference_from_payload(obj) -> dict:
    entry: dict = {}
    if getattr(obj, "reference", None):
        entry["reference"] = obj.reference
    if getattr(obj, "reference_display", None):
        entry["display"] = obj.reference_display
    return entry


def _reference_with_identifier_fallback_from_payload(obj) -> dict:
    entry = _reference_from_payload(obj)
    id_use = getattr(obj, "reference_identifier_use", None)
    id_type_system = getattr(obj, "reference_identifier_type_system", None)
    id_type_code = getattr(obj, "reference_identifier_type_code", None)
    id_type_text = getattr(obj, "reference_identifier_type_text", None)
    id_system = getattr(obj, "reference_identifier_system", None)
    id_value = getattr(obj, "reference_identifier_value", None)
    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
        identifier: dict = {}
        if id_use:
            identifier["use"] = id_use.value if hasattr(id_use, "value") else id_use
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
                type_cc["coding"] = [
                    {
                        k: v
                        for k, v in {
                            "system": id_type_system,
                            "version": getattr(obj, "reference_identifier_type_version", None),
                            "code": id_type_code,
                            "display": getattr(obj, "reference_identifier_type_display", None),
                            "userSelected": getattr(obj, "reference_identifier_type_user_selected", None),
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
        period = _period(
            getattr(obj, "reference_identifier_period_start", None),
            getattr(obj, "reference_identifier_period_end", None),
        )
        if period:
            identifier["period"] = period
        entry["identifier"] = identifier
    return entry


def payload_observation_identifier(i: ObservationIdentifierInput) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = i.use.value
    coding = _coding_list(i.type_coding)
    if coding or i.type_text:
        type_cc: dict = {}
        if coding:
            type_cc["coding"] = coding
        if i.type_text:
            type_cc["text"] = i.type_text
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    period = _period(i.period_start, i.period_end)
    if period:
        entry["period"] = period
    if i.assigner:
        assigner: dict = {"reference": i.assigner}
        if i.assigner_display:
            assigner["display"] = i.assigner_display
        entry["assigner"] = assigner
    return entry


def payload_observation_codeable_concept(cc: ObservationCodeableConceptInput) -> dict:
    entry: dict = {}
    coding = _coding_list(cc.coding)
    if coding:
        entry["coding"] = coding
    if cc.text:
        entry["text"] = cc.text
    return entry


def payload_observation_note(n: ObservationNoteInput) -> dict:
    entry: dict = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    elif n.author_reference:
        ref: dict = {"reference": n.author_reference}
        if n.author_reference_display:
            ref["display"] = n.author_reference_display
        entry["authorReference"] = ref
    if n.time:
        entry["time"] = n.time.isoformat()
    if n.text:
        entry["text"] = n.text
    return entry


def _value_x_from_payload(obj, out: dict) -> None:
    """Renders the 11-variant value[x] choice (shared shape between the
    root resource and its own component) directly into `out`."""
    qty = {
        k: v
        for k, v in {
            "value": obj.value_quantity_value,
            "comparator": obj.value_quantity_comparator.value if obj.value_quantity_comparator else None,
            "unit": obj.value_quantity_unit,
            "system": obj.value_quantity_system,
            "code": obj.value_quantity_code,
        }.items()
        if v is not None
    }
    if qty:
        out["valueQuantity"] = qty
        return
    value_cc = getattr(obj, "value_codeable_concept", None)
    if value_cc:
        cc = payload_observation_codeable_concept(value_cc)
        if cc:
            out["valueCodeableConcept"] = cc
            return
    if obj.value_string:
        out["valueString"] = obj.value_string
        return
    if obj.value_boolean is not None:
        out["valueBoolean"] = obj.value_boolean
        return
    if obj.value_integer is not None:
        out["valueInteger"] = obj.value_integer
        return
    range_low = {
        k: v
        for k, v in {
            "value": obj.value_range_low_value, "unit": obj.value_range_low_unit,
            "system": obj.value_range_low_system, "code": obj.value_range_low_code,
        }.items()
        if v is not None
    }
    range_high = {
        k: v
        for k, v in {
            "value": obj.value_range_high_value, "unit": obj.value_range_high_unit,
            "system": obj.value_range_high_system, "code": obj.value_range_high_code,
        }.items()
        if v is not None
    }
    if range_low or range_high:
        range_entry: dict = {}
        if range_low:
            range_entry["low"] = range_low
        if range_high:
            range_entry["high"] = range_high
        out["valueRange"] = range_entry
        return
    ratio_num = {
        k: v
        for k, v in {
            "value": obj.value_ratio_numerator_value,
            "comparator": obj.value_ratio_numerator_comparator.value if obj.value_ratio_numerator_comparator else None,
            "unit": obj.value_ratio_numerator_unit, "system": obj.value_ratio_numerator_system,
            "code": obj.value_ratio_numerator_code,
        }.items()
        if v is not None
    }
    ratio_den = {
        k: v
        for k, v in {
            "value": obj.value_ratio_denominator_value,
            "comparator": obj.value_ratio_denominator_comparator.value if obj.value_ratio_denominator_comparator else None,
            "unit": obj.value_ratio_denominator_unit, "system": obj.value_ratio_denominator_system,
            "code": obj.value_ratio_denominator_code,
        }.items()
        if v is not None
    }
    if ratio_num or ratio_den:
        ratio_entry: dict = {}
        if ratio_num:
            ratio_entry["numerator"] = ratio_num
        if ratio_den:
            ratio_entry["denominator"] = ratio_den
        out["valueRatio"] = ratio_entry
        return
    sampled_origin = {
        k: v
        for k, v in {
            "value": obj.value_sampled_data_origin_value, "unit": obj.value_sampled_data_origin_unit,
            "system": obj.value_sampled_data_origin_system, "code": obj.value_sampled_data_origin_code,
        }.items()
        if v is not None
    }
    if sampled_origin or obj.value_sampled_data_period is not None or obj.value_sampled_data_dimensions is not None:
        sampled: dict = {}
        if sampled_origin:
            sampled["origin"] = sampled_origin
        if obj.value_sampled_data_period is not None:
            sampled["period"] = obj.value_sampled_data_period
        if obj.value_sampled_data_factor is not None:
            sampled["factor"] = obj.value_sampled_data_factor
        if obj.value_sampled_data_lower_limit is not None:
            sampled["lowerLimit"] = obj.value_sampled_data_lower_limit
        if obj.value_sampled_data_upper_limit is not None:
            sampled["upperLimit"] = obj.value_sampled_data_upper_limit
        if obj.value_sampled_data_dimensions is not None:
            sampled["dimensions"] = obj.value_sampled_data_dimensions
        if obj.value_sampled_data_data:
            sampled["data"] = obj.value_sampled_data_data
        out["valueSampledData"] = sampled
        return
    if obj.value_time:
        out["valueTime"] = obj.value_time.isoformat()
        return
    if obj.value_date_time:
        out["valueDateTime"] = obj.value_date_time.isoformat()
        return
    period = _period(obj.value_period_start, obj.value_period_end)
    if period:
        out["valuePeriod"] = period


def _reference_range_choice(rr: ObservationReferenceRangeInput) -> dict:
    entry: dict = {}
    low = {
        k: v
        for k, v in {
            "value": rr.low_value, "unit": rr.low_unit, "system": rr.low_system, "code": rr.low_code,
        }.items()
        if v is not None
    }
    if low:
        entry["low"] = low
    high = {
        k: v
        for k, v in {
            "value": rr.high_value, "unit": rr.high_unit, "system": rr.high_system, "code": rr.high_code,
        }.items()
        if v is not None
    }
    if high:
        entry["high"] = high
    if rr.type:
        type_cc = payload_observation_codeable_concept(rr.type)
        if type_cc:
            entry["type"] = type_cc
    if rr.applies_to:
        applies_tos = [payload_observation_codeable_concept(a) for a in rr.applies_to]
        applies_tos = [a for a in applies_tos if a]
        if applies_tos:
            entry["appliesTo"] = applies_tos
    age_low = {
        k: v
        for k, v in {
            "value": rr.age_low_value, "unit": rr.age_low_unit, "system": rr.age_low_system, "code": rr.age_low_code,
        }.items()
        if v is not None
    }
    age_high = {
        k: v
        for k, v in {
            "value": rr.age_high_value, "unit": rr.age_high_unit, "system": rr.age_high_system, "code": rr.age_high_code,
        }.items()
        if v is not None
    }
    if age_low or age_high:
        age: dict = {}
        if age_low:
            age["low"] = age_low
        if age_high:
            age["high"] = age_high
        entry["age"] = age
    if rr.text:
        entry["text"] = rr.text
    return entry


def payload_observation_component(c: ObservationComponentInput) -> dict:
    entry: dict = {"code": payload_observation_codeable_concept(c.code)}
    _value_x_from_payload(c, entry)
    if c.data_absent_reason:
        dar = payload_observation_codeable_concept(c.data_absent_reason)
        if dar:
            entry["dataAbsentReason"] = dar
    if c.interpretation:
        interpretations = [payload_observation_codeable_concept(i) for i in c.interpretation]
        interpretations = [i for i in interpretations if i]
        if interpretations:
            entry["interpretation"] = interpretations
    if c.reference_range:
        reference_ranges = [_reference_range_choice(rr) for rr in c.reference_range]
        reference_ranges = [rr for rr in reference_ranges if rr]
        if reference_ranges:
            entry["referenceRange"] = reference_ranges
    return entry


# field -> (fhir key, builder) for every plain 0..* list on this resource.
_LIST_FIELDS = {
    "identifier": ("identifier", payload_observation_identifier),
    "based_on": ("basedOn", _reference_with_identifier_fallback_from_payload),
    "part_of": ("partOf", _reference_with_identifier_fallback_from_payload),
    "category": ("category", payload_observation_codeable_concept),
    "focus": ("focus", _reference_with_identifier_fallback_from_payload),
    "performer": ("performer", _reference_with_identifier_fallback_from_payload),
    "interpretation": ("interpretation", payload_observation_codeable_concept),
    "note": ("note", payload_observation_note),
    "reference_range": ("referenceRange", _reference_range_choice),
    "has_member": ("hasMember", _reference_with_identifier_fallback_from_payload),
    "derived_from": ("derivedFrom", _reference_with_identifier_fallback_from_payload),
    "component": ("component", payload_observation_component),
}

_SINGLE_REFERENCE_FIELDS = {
    "subject": "subject",
    "encounter": "encounter",
    "specimen": "specimen",
    "device": "device",
}
_SINGLE_CC_FIELDS = {
    "data_absent_reason": "dataAbsentReason",
    "body_site": "bodySite",
    "method": "method",
}

_EFFECTIVE_FIELDS = {
    "effective_date_time", "effective_period_start", "effective_period_end",
    "effective_timing", "effective_instant",
}
_VALUE_X_FIELDS = {
    "value_quantity_value", "value_quantity_comparator", "value_quantity_unit", "value_quantity_system",
    "value_quantity_code", "value_codeable_concept", "value_string", "value_boolean", "value_integer",
    "value_range_low_value", "value_range_low_unit", "value_range_low_system", "value_range_low_code",
    "value_range_high_value", "value_range_high_unit", "value_range_high_system", "value_range_high_code",
    "value_ratio_numerator_value", "value_ratio_numerator_comparator", "value_ratio_numerator_unit",
    "value_ratio_numerator_system", "value_ratio_numerator_code", "value_ratio_denominator_value",
    "value_ratio_denominator_comparator", "value_ratio_denominator_unit", "value_ratio_denominator_system",
    "value_ratio_denominator_code", "value_sampled_data_origin_value", "value_sampled_data_origin_unit",
    "value_sampled_data_origin_system", "value_sampled_data_origin_code", "value_sampled_data_period",
    "value_sampled_data_factor", "value_sampled_data_lower_limit", "value_sampled_data_upper_limit",
    "value_sampled_data_dimensions", "value_sampled_data_data", "value_time", "value_date_time",
    "value_period_start", "value_period_end",
}


def _effective_choice(payload) -> tuple[str, object] | None:
    if payload.effective_date_time:
        return "effectiveDateTime", payload.effective_date_time.isoformat()
    period = _period(payload.effective_period_start, payload.effective_period_end)
    if period:
        return "effectivePeriod", period
    if payload.effective_timing:
        return "effectiveTiming", dict(payload.effective_timing)
    if payload.effective_instant:
        return "effectiveInstant", payload.effective_instant.isoformat()
    return None


def payload_to_fhir_observation(payload: ObservationCreateSchema) -> dict:
    """Full-resource conversion for CREATE: every field is considered present."""
    result: dict = {"resourceType": "Observation"}

    if payload.extension:
        result["extension"] = list(payload.extension)

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        items = [i for i in items if i]
        if items:
            result[fhir_key] = items

    if payload.status:
        result["status"] = payload.status.value

    result["code"] = payload_observation_codeable_concept(payload.code)

    for field, fhir_key in _SINGLE_REFERENCE_FIELDS.items():
        obj = getattr(payload, field, None)
        if obj:
            ref = _reference_with_identifier_fallback_from_payload(obj)
            if ref:
                result[fhir_key] = ref

    effective = _effective_choice(payload)
    if effective:
        result[effective[0]] = effective[1]

    if payload.issued:
        result["issued"] = payload.issued.isoformat()

    _value_x_from_payload(payload, result)

    for field, fhir_key in _SINGLE_CC_FIELDS.items():
        obj = getattr(payload, field, None)
        if obj:
            cc = payload_observation_codeable_concept(obj)
            if cc:
                result[fhir_key] = cc

    return result


def patch_fragment_to_fhir_observation(payload: ObservationPatchSchema) -> tuple[dict, set[str]]:
    """Tri-state conversion for PATCH."""
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = list(payload.extension)

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            items = [builder(item) for item in (getattr(payload, field, None) or [])]
            items = [i for i in items if i]
            if items:
                fragment[fhir_key] = items

    if "status" in provided:
        touched.add("status")
        if payload.status:
            fragment["status"] = payload.status.value

    if "code" in provided:
        touched.add("code")
        if payload.code:
            cc = payload_observation_codeable_concept(payload.code)
            if cc:
                fragment["code"] = cc

    for field, fhir_key in _SINGLE_REFERENCE_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            obj = getattr(payload, field, None)
            if obj:
                ref = _reference_with_identifier_fallback_from_payload(obj)
                if ref:
                    fragment[fhir_key] = ref

    if provided & _EFFECTIVE_FIELDS:
        touched.update({"effectiveDateTime", "effectivePeriod", "effectiveTiming", "effectiveInstant"})
        effective = _effective_choice(payload)
        if effective:
            fragment[effective[0]] = effective[1]

    if "issued" in provided:
        touched.add("issued")
        if payload.issued:
            fragment["issued"] = payload.issued.isoformat()

    if provided & _VALUE_X_FIELDS:
        touched.update({
            "valueQuantity", "valueCodeableConcept", "valueString", "valueBoolean", "valueInteger",
            "valueRange", "valueRatio", "valueSampledData", "valueTime", "valueDateTime", "valuePeriod",
        })
        _value_x_from_payload(payload, fragment)

    for field, fhir_key in _SINGLE_CC_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            obj = getattr(payload, field, None)
            if obj:
                cc = payload_observation_codeable_concept(obj)
                if cc:
                    fragment[fhir_key] = cc

    return fragment, touched
