from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.observation import ObservationModel


def _plain_reference(obj, prefix: str) -> dict | None:
    ref = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)
    if not (ref or ref_type or ref_id or display):
        return None
    return {
        "reference": ref,
        "reference_type": fhir_enum(ref_type) if ref_type else None,
        "reference_id": ref_id,
        "reference_display": display,
    }


def _plain_reference_row(obj, row_id: int) -> dict:
    return {
        "id": row_id,
        "reference": obj.reference_reference,
        "reference_type": fhir_enum(obj.reference_type) if obj.reference_type else None,
        "reference_id": obj.reference_id,
        "reference_display": obj.reference_display,
    }


def _plain_identifier(obj, prefix: str = "") -> dict | None:
    p = prefix
    use = getattr(obj, f"{p}use", None)
    type_text = getattr(obj, f"{p}type_text", None)
    system = getattr(obj, f"{p}system", None)
    value = getattr(obj, f"{p}value", None)
    assigner_reference = getattr(obj, f"{p}assigner_reference", None)
    assigner_id = getattr(obj, f"{p}assigner_id", None)
    codings_attr = f"{p}type_codings" if p else "type_codings"
    codings = getattr(obj, codings_attr, None)
    if not (use or type_text or system or value or codings or assigner_reference or assigner_id):
        return None
    assigner_type = getattr(obj, f"{p}assigner_type", None)
    period_start = getattr(obj, f"{p}period_start", None)
    period_end = getattr(obj, f"{p}period_end", None)
    return {
        "use": fhir_enum(use) if use else None,
        "type_codings": [
            {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "user_selected": c.user_selected,
            }
            for c in (codings or [])
        ]
        or None,
        "type_text": type_text,
        "system": system,
        "value": value,
        "period_start": period_start.isoformat() if period_start else None,
        "period_end": period_end.isoformat() if period_end else None,
        "assigner": assigner_reference
        or (f"{fhir_enum(assigner_type)}/{assigner_id}" if assigner_type and assigner_id else None),
        "assigner_id": assigner_id,
        "assigner_display": getattr(obj, f"{p}assigner_display", None),
        "assigner_identifier_use": (
            fhir_enum(v) if (v := getattr(obj, f"{p}assigner_identifier_use", None)) else None
        ),
        "assigner_identifier_type_system": getattr(obj, f"{p}assigner_identifier_type_system", None),
        "assigner_identifier_type_version": getattr(obj, f"{p}assigner_identifier_type_version", None),
        "assigner_identifier_type_code": getattr(obj, f"{p}assigner_identifier_type_code", None),
        "assigner_identifier_type_display": getattr(obj, f"{p}assigner_identifier_type_display", None),
        "assigner_identifier_type_text": getattr(obj, f"{p}assigner_identifier_type_text", None),
        "assigner_identifier_type_user_selected": getattr(obj, f"{p}assigner_identifier_type_user_selected", None),
        "assigner_identifier_system": getattr(obj, f"{p}assigner_identifier_system", None),
        "assigner_identifier_value": getattr(obj, f"{p}assigner_identifier_value", None),
        "assigner_identifier_period_start": (
            v.isoformat() if (v := getattr(obj, f"{p}assigner_identifier_period_start", None)) else None
        ),
        "assigner_identifier_period_end": (
            v.isoformat() if (v := getattr(obj, f"{p}assigner_identifier_period_end", None)) else None
        ),
    }


def _plain_codeable_concept(codings, text: str | None) -> dict | None:
    if not (codings or text):
        return None
    return {
        "codings": [
            {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "user_selected": c.user_selected,
            }
            for c in (codings or [])
        ]
        or None,
        "text": text,
    }


def _plain_note(n) -> dict:
    return {
        "id": n.id,
        "author_string": n.author_string,
        "author_reference": n.author_reference,
        "author_reference_type": fhir_enum(n.author_type) if n.author_type else None,
        "author_id": n.author_id,
        "author_display": n.author_display,
        "time": n.time.isoformat() if n.time else None,
        "text": n.text,
    }


def _plain_reference_range(rr) -> dict:
    return {
        "id": rr.id,
        "low_value": float(rr.low_value) if rr.low_value is not None else None,
        "low_unit": rr.low_unit,
        "low_system": rr.low_system,
        "low_code": rr.low_code,
        "high_value": float(rr.high_value) if rr.high_value is not None else None,
        "high_unit": rr.high_unit,
        "high_system": rr.high_system,
        "high_code": rr.high_code,
        "type_codings": [
            {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "user_selected": c.user_selected,
            }
            for c in (rr.type_codings or [])
        ]
        or None,
        "type_text": rr.type_text,
        "applies_to": [
            {**(_plain_codeable_concept(a.codings, a.text) or {}), "id": a.id} for a in (rr.applies_tos or [])
        ]
        or None,
        "age_low_value": float(rr.age_low_value) if rr.age_low_value is not None else None,
        "age_low_unit": rr.age_low_unit,
        "age_low_system": rr.age_low_system,
        "age_low_code": rr.age_low_code,
        "age_high_value": float(rr.age_high_value) if rr.age_high_value is not None else None,
        "age_high_unit": rr.age_high_unit,
        "age_high_system": rr.age_high_system,
        "age_high_code": rr.age_high_code,
        "text": rr.text,
    }


def _plain_component(c) -> dict:
    return {
        "id": c.id,
        "code_codings": [
            {
                "system": cd.system,
                "version": cd.version,
                "code": cd.code,
                "display": cd.display,
                "user_selected": cd.user_selected,
            }
            for cd in (c.code_codings or [])
        ]
        or None,
        "code_text": c.code_text,
        "value_quantity_value": float(c.value_quantity_value) if c.value_quantity_value is not None else None,
        "value_quantity_comparator": fhir_enum(c.value_quantity_comparator) if c.value_quantity_comparator else None,
        "value_quantity_unit": c.value_quantity_unit,
        "value_quantity_system": c.value_quantity_system,
        "value_quantity_code": c.value_quantity_code,
        "value_codeable_concept_codings": [
            {
                "system": cd.system,
                "version": cd.version,
                "code": cd.code,
                "display": cd.display,
                "user_selected": cd.user_selected,
            }
            for cd in (c.value_codeable_concept_codings or [])
        ]
        or None,
        "value_codeable_concept_text": c.value_codeable_concept_text,
        "value_string": c.value_string,
        "value_boolean": c.value_boolean,
        "value_integer": c.value_integer,
        "value_range_low_value": float(c.value_range_low_value) if c.value_range_low_value is not None else None,
        "value_range_low_unit": c.value_range_low_unit,
        "value_range_low_system": c.value_range_low_system,
        "value_range_low_code": c.value_range_low_code,
        "value_range_high_value": float(c.value_range_high_value) if c.value_range_high_value is not None else None,
        "value_range_high_unit": c.value_range_high_unit,
        "value_range_high_system": c.value_range_high_system,
        "value_range_high_code": c.value_range_high_code,
        "value_ratio_numerator_value": float(c.value_ratio_numerator_value) if c.value_ratio_numerator_value is not None else None,
        "value_ratio_numerator_comparator": fhir_enum(c.value_ratio_numerator_comparator) if c.value_ratio_numerator_comparator else None,
        "value_ratio_numerator_unit": c.value_ratio_numerator_unit,
        "value_ratio_numerator_system": c.value_ratio_numerator_system,
        "value_ratio_numerator_code": c.value_ratio_numerator_code,
        "value_ratio_denominator_value": float(c.value_ratio_denominator_value) if c.value_ratio_denominator_value is not None else None,
        "value_ratio_denominator_comparator": fhir_enum(c.value_ratio_denominator_comparator) if c.value_ratio_denominator_comparator else None,
        "value_ratio_denominator_unit": c.value_ratio_denominator_unit,
        "value_ratio_denominator_system": c.value_ratio_denominator_system,
        "value_ratio_denominator_code": c.value_ratio_denominator_code,
        "value_sampled_data_origin_value": float(c.value_sampled_data_origin_value) if c.value_sampled_data_origin_value is not None else None,
        "value_sampled_data_origin_unit": c.value_sampled_data_origin_unit,
        "value_sampled_data_origin_system": c.value_sampled_data_origin_system,
        "value_sampled_data_origin_code": c.value_sampled_data_origin_code,
        "value_sampled_data_period": float(c.value_sampled_data_period) if c.value_sampled_data_period is not None else None,
        "value_sampled_data_factor": float(c.value_sampled_data_factor) if c.value_sampled_data_factor is not None else None,
        "value_sampled_data_lower_limit": float(c.value_sampled_data_lower_limit) if c.value_sampled_data_lower_limit is not None else None,
        "value_sampled_data_upper_limit": float(c.value_sampled_data_upper_limit) if c.value_sampled_data_upper_limit is not None else None,
        "value_sampled_data_dimensions": c.value_sampled_data_dimensions,
        "value_sampled_data_data": c.value_sampled_data_data,
        "value_time": c.value_time.isoformat() if c.value_time else None,
        "value_date_time": c.value_date_time.isoformat() if c.value_date_time else None,
        "value_period_start": c.value_period_start.isoformat() if c.value_period_start else None,
        "value_period_end": c.value_period_end.isoformat() if c.value_period_end else None,
        "data_absent_reason_codings": [
            {
                "system": cd.system,
                "version": cd.version,
                "code": cd.code,
                "display": cd.display,
                "user_selected": cd.user_selected,
            }
            for cd in (c.data_absent_reason_codings or [])
        ]
        or None,
        "data_absent_reason_text": c.data_absent_reason_text,
        "interpretation": [
            {**(_plain_codeable_concept(i.codings, i.text) or {}), "id": i.id} for i in (c.interpretations or [])
        ]
        or None,
        "reference_range": [_plain_reference_range(rr) for rr in (c.reference_ranges or [])] or None,
    }


def to_plain_observation(obs: ObservationModel) -> dict:
    result = {
        "id": obs.observation_id,
        "extension": list(obs.extension) if obs.extension else None,
        "identifier": [
            {**(_plain_identifier(i) or {}), "id": i.id} for i in (obs.identifiers or [])
        ]
        or None,
        "based_on": [_plain_reference_row(b, b.id) for b in (obs.based_ons or [])] or None,
        "part_of": [_plain_reference_row(p, p.id) for p in (obs.part_ofs or [])] or None,
        "status": fhir_enum(obs.status).replace("_", "-") if obs.status else None,
        "category": [
            {**(_plain_codeable_concept(c.codings, c.text) or {}), "id": c.id} for c in (obs.categories or [])
        ]
        or None,
        "code_codings": [
            {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "user_selected": c.user_selected,
            }
            for c in (obs.code_codings or [])
        ]
        or None,
        "code_text": obs.code_text,
        "subject": _plain_reference(obs, "subject"),
        "focus": [_plain_reference_row(f, f.id) for f in (obs.focuses or [])] or None,
        "encounter": _plain_reference(obs, "encounter"),
        "effective_date_time": obs.effective_date_time.isoformat() if obs.effective_date_time else None,
        "effective_period_start": obs.effective_period_start.isoformat() if obs.effective_period_start else None,
        "effective_period_end": obs.effective_period_end.isoformat() if obs.effective_period_end else None,
        "effective_timing": dict(obs.effective_timing) if obs.effective_timing else None,
        "effective_instant": obs.effective_instant.isoformat() if obs.effective_instant else None,
        "issued": obs.issued.isoformat() if obs.issued else None,
        "performer": [_plain_reference_row(p, p.id) for p in (obs.performers or [])] or None,
        "value_quantity_value": float(obs.value_quantity_value) if obs.value_quantity_value is not None else None,
        "value_quantity_comparator": fhir_enum(obs.value_quantity_comparator) if obs.value_quantity_comparator else None,
        "value_quantity_unit": obs.value_quantity_unit,
        "value_quantity_system": obs.value_quantity_system,
        "value_quantity_code": obs.value_quantity_code,
        "value_codeable_concept": _plain_codeable_concept(obs.value_codeable_concept_codings, obs.value_codeable_concept_text),
        "value_string": obs.value_string,
        "value_boolean": obs.value_boolean,
        "value_integer": obs.value_integer,
        "value_range_low_value": float(obs.value_range_low_value) if obs.value_range_low_value is not None else None,
        "value_range_low_unit": obs.value_range_low_unit,
        "value_range_low_system": obs.value_range_low_system,
        "value_range_low_code": obs.value_range_low_code,
        "value_range_high_value": float(obs.value_range_high_value) if obs.value_range_high_value is not None else None,
        "value_range_high_unit": obs.value_range_high_unit,
        "value_range_high_system": obs.value_range_high_system,
        "value_range_high_code": obs.value_range_high_code,
        "value_ratio_numerator_value": float(obs.value_ratio_numerator_value) if obs.value_ratio_numerator_value is not None else None,
        "value_ratio_numerator_comparator": fhir_enum(obs.value_ratio_numerator_comparator) if obs.value_ratio_numerator_comparator else None,
        "value_ratio_numerator_unit": obs.value_ratio_numerator_unit,
        "value_ratio_numerator_system": obs.value_ratio_numerator_system,
        "value_ratio_numerator_code": obs.value_ratio_numerator_code,
        "value_ratio_denominator_value": float(obs.value_ratio_denominator_value) if obs.value_ratio_denominator_value is not None else None,
        "value_ratio_denominator_comparator": fhir_enum(obs.value_ratio_denominator_comparator) if obs.value_ratio_denominator_comparator else None,
        "value_ratio_denominator_unit": obs.value_ratio_denominator_unit,
        "value_ratio_denominator_system": obs.value_ratio_denominator_system,
        "value_ratio_denominator_code": obs.value_ratio_denominator_code,
        "value_sampled_data_origin_value": float(obs.value_sampled_data_origin_value) if obs.value_sampled_data_origin_value is not None else None,
        "value_sampled_data_origin_unit": obs.value_sampled_data_origin_unit,
        "value_sampled_data_origin_system": obs.value_sampled_data_origin_system,
        "value_sampled_data_origin_code": obs.value_sampled_data_origin_code,
        "value_sampled_data_period": float(obs.value_sampled_data_period) if obs.value_sampled_data_period is not None else None,
        "value_sampled_data_factor": float(obs.value_sampled_data_factor) if obs.value_sampled_data_factor is not None else None,
        "value_sampled_data_lower_limit": float(obs.value_sampled_data_lower_limit) if obs.value_sampled_data_lower_limit is not None else None,
        "value_sampled_data_upper_limit": float(obs.value_sampled_data_upper_limit) if obs.value_sampled_data_upper_limit is not None else None,
        "value_sampled_data_dimensions": obs.value_sampled_data_dimensions,
        "value_sampled_data_data": obs.value_sampled_data_data,
        "value_time": obs.value_time.isoformat() if obs.value_time else None,
        "value_date_time": obs.value_date_time.isoformat() if obs.value_date_time else None,
        "value_period_start": obs.value_period_start.isoformat() if obs.value_period_start else None,
        "value_period_end": obs.value_period_end.isoformat() if obs.value_period_end else None,
        "data_absent_reason": _plain_codeable_concept(obs.data_absent_reason_codings, obs.data_absent_reason_text),
        "interpretation": [
            {**(_plain_codeable_concept(i.codings, i.text) or {}), "id": i.id} for i in (obs.interpretations or [])
        ]
        or None,
        "note": [_plain_note(n) for n in (obs.notes or [])] or None,
        "body_site": _plain_codeable_concept(obs.body_site_codings, obs.body_site_text),
        "method": _plain_codeable_concept(obs.method_codings, obs.method_text),
        "specimen": _plain_reference(obs, "specimen"),
        "device": _plain_reference(obs, "device"),
        "reference_range": [_plain_reference_range(rr) for rr in (obs.reference_ranges or [])] or None,
        "has_member": [_plain_reference_row(h, h.id) for h in (obs.has_members or [])] or None,
        "derived_from": [_plain_reference_row(d, d.id) for d in (obs.derived_froms or [])] or None,
        "component": [_plain_component(c) for c in (obs.components or [])] or None,
        "user_id": obs.user_id,
        "org_id": obs.tenant_id,
        "created_at": obs.created_at.isoformat() if obs.created_at else None,
        "updated_at": obs.updated_at.isoformat() if obs.updated_at else None,
        "created_by": obs.created_by,
        "updated_by": obs.updated_by,
    }
    return {k: v for k, v in result.items() if v is not None}
