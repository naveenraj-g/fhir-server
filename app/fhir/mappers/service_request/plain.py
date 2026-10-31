from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.service_request import ServiceRequestModel


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


def to_plain_service_request(sr: ServiceRequestModel) -> dict:
    result = {
        "id": sr.service_request_id,
        "extension": list(sr.extension) if sr.extension else None,
        "identifier": [
            {**(_plain_identifier(i) or {}), "id": i.id} for i in (sr.identifiers or [])
        ]
        or None,
        "instantiates_canonical": list(sr.instantiates_canonical) if sr.instantiates_canonical else None,
        "instantiates_uri": list(sr.instantiates_uri) if sr.instantiates_uri else None,
        "based_on": [_plain_reference_row(b, b.id) for b in (sr.based_ons or [])] or None,
        "replaces": [_plain_reference_row(r, r.id) for r in (sr.replaces or [])] or None,
        "requisition": _plain_identifier(sr, "requisition_"),
        "status": fhir_enum(sr.status).replace("_", "-") if sr.status else None,
        "intent": fhir_enum(sr.intent).replace("_", "-") if sr.intent else None,
        "category": [
            {**(_plain_codeable_concept(c.codings, c.text) or {}), "id": c.id} for c in (sr.categories or [])
        ]
        or None,
        "priority": fhir_enum(sr.priority) if sr.priority else None,
        "do_not_perform": sr.do_not_perform,
        "code": _plain_codeable_concept(sr.code_codings, sr.code_text),
        "order_detail": [
            {**(_plain_codeable_concept(o.codings, o.text) or {}), "id": o.id} for o in (sr.order_details or [])
        ]
        or None,
        "quantity_quantity_value": float(sr.quantity_quantity_value) if sr.quantity_quantity_value is not None else None,
        "quantity_quantity_comparator": fhir_enum(sr.quantity_quantity_comparator) if sr.quantity_quantity_comparator else None,
        "quantity_quantity_unit": sr.quantity_quantity_unit,
        "quantity_quantity_system": sr.quantity_quantity_system,
        "quantity_quantity_code": sr.quantity_quantity_code,
        "quantity_ratio_numerator_value": float(sr.quantity_ratio_numerator_value) if sr.quantity_ratio_numerator_value is not None else None,
        "quantity_ratio_numerator_comparator": fhir_enum(sr.quantity_ratio_numerator_comparator) if sr.quantity_ratio_numerator_comparator else None,
        "quantity_ratio_numerator_unit": sr.quantity_ratio_numerator_unit,
        "quantity_ratio_numerator_system": sr.quantity_ratio_numerator_system,
        "quantity_ratio_numerator_code": sr.quantity_ratio_numerator_code,
        "quantity_ratio_denominator_value": float(sr.quantity_ratio_denominator_value) if sr.quantity_ratio_denominator_value is not None else None,
        "quantity_ratio_denominator_comparator": fhir_enum(sr.quantity_ratio_denominator_comparator) if sr.quantity_ratio_denominator_comparator else None,
        "quantity_ratio_denominator_unit": sr.quantity_ratio_denominator_unit,
        "quantity_ratio_denominator_system": sr.quantity_ratio_denominator_system,
        "quantity_ratio_denominator_code": sr.quantity_ratio_denominator_code,
        "quantity_range_low_value": float(sr.quantity_range_low_value) if sr.quantity_range_low_value is not None else None,
        "quantity_range_low_unit": sr.quantity_range_low_unit,
        "quantity_range_low_system": sr.quantity_range_low_system,
        "quantity_range_low_code": sr.quantity_range_low_code,
        "quantity_range_high_value": float(sr.quantity_range_high_value) if sr.quantity_range_high_value is not None else None,
        "quantity_range_high_unit": sr.quantity_range_high_unit,
        "quantity_range_high_system": sr.quantity_range_high_system,
        "quantity_range_high_code": sr.quantity_range_high_code,
        "subject": _plain_reference(sr, "subject"),
        "encounter": _plain_reference(sr, "encounter"),
        "occurrence_date_time": sr.occurrence_date_time.isoformat() if sr.occurrence_date_time else None,
        "occurrence_period_start": sr.occurrence_period_start.isoformat() if sr.occurrence_period_start else None,
        "occurrence_period_end": sr.occurrence_period_end.isoformat() if sr.occurrence_period_end else None,
        "occurrence_timing": dict(sr.occurrence_timing) if sr.occurrence_timing else None,
        "as_needed_boolean": sr.as_needed_boolean,
        "as_needed_codeable_concept": _plain_codeable_concept(sr.as_needed_codings, sr.as_needed_codeable_concept_text),
        "authored_on": sr.authored_on.isoformat() if sr.authored_on else None,
        "requester": _plain_reference(sr, "requester"),
        "performer_type": _plain_codeable_concept(sr.performer_type_codings, sr.performer_type_text),
        "performer": [_plain_reference_row(p, p.id) for p in (sr.performers or [])] or None,
        "location_code": [
            {**(_plain_codeable_concept(lc.codings, lc.text) or {}), "id": lc.id} for lc in (sr.location_codes or [])
        ]
        or None,
        "location_reference": [_plain_reference_row(lr, lr.id) for lr in (sr.location_references or [])] or None,
        "reason_code": [
            {**(_plain_codeable_concept(rc.codings, rc.text) or {}), "id": rc.id} for rc in (sr.reason_codes or [])
        ]
        or None,
        "reason_reference": [_plain_reference_row(rr, rr.id) for rr in (sr.reason_references or [])] or None,
        "insurance": [_plain_reference_row(ins, ins.id) for ins in (sr.insurances or [])] or None,
        "supporting_info": [_plain_reference_row(si, si.id) for si in (sr.supporting_infos or [])] or None,
        "specimen": [_plain_reference_row(sp, sp.id) for sp in (sr.specimens or [])] or None,
        "body_site": [
            {**(_plain_codeable_concept(bs.codings, bs.text) or {}), "id": bs.id} for bs in (sr.body_sites or [])
        ]
        or None,
        "note": [_plain_note(n) for n in (sr.notes or [])] or None,
        "patient_instruction": sr.patient_instruction,
        "relevant_history": [_plain_reference_row(rh, rh.id) for rh in (sr.relevant_histories or [])] or None,
        "org_id": sr.tenant_id,
        "created_at": sr.created_at.isoformat() if sr.created_at else None,
        "updated_at": sr.updated_at.isoformat() if sr.updated_at else None,
        "created_by": sr.created_by,
        "updated_by": sr.updated_by,
    }
    return {k: v for k, v in result.items() if v is not None}
