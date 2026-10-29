from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.medication_request import MedicationRequestModel


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


def _plain_dosage_instruction(d) -> dict:
    return {
        "id": d.id,
        "sequence": d.sequence,
        "text": d.text,
        "additional_instruction": [
            {**(_plain_codeable_concept(ai.codings, ai.text) or {}), "id": ai.id}
            for ai in (d.additional_instructions or [])
        ]
        or None,
        "patient_instruction": d.patient_instruction,
        "timing": dict(d.timing) if d.timing else None,
        "as_needed_boolean": d.as_needed_boolean,
        "as_needed_codeable_concept": _plain_codeable_concept(d.as_needed_codings, d.as_needed_codeable_concept_text),
        "site": _plain_codeable_concept(d.site_codings, d.site_text),
        "route": _plain_codeable_concept(d.route_codings, d.route_text),
        "method": _plain_codeable_concept(d.method_codings, d.method_text),
        "dose_and_rate": list(d.dose_and_rate) if d.dose_and_rate else None,
        "max_dose_per_period": dict(d.max_dose_per_period) if d.max_dose_per_period else None,
        "max_dose_per_administration_value": float(d.max_dose_per_administration_value) if d.max_dose_per_administration_value is not None else None,
        "max_dose_per_administration_unit": d.max_dose_per_administration_unit,
        "max_dose_per_administration_system": d.max_dose_per_administration_system,
        "max_dose_per_administration_code": d.max_dose_per_administration_code,
        "max_dose_per_lifetime_value": float(d.max_dose_per_lifetime_value) if d.max_dose_per_lifetime_value is not None else None,
        "max_dose_per_lifetime_unit": d.max_dose_per_lifetime_unit,
        "max_dose_per_lifetime_system": d.max_dose_per_lifetime_system,
        "max_dose_per_lifetime_code": d.max_dose_per_lifetime_code,
    }


def _plain_dispense_request(mr: MedicationRequestModel) -> dict | None:
    performer = _plain_reference(mr, "dispense_request_performer")
    result = {
        "initial_fill_quantity_value": float(mr.dispense_request_initial_fill_quantity_value) if mr.dispense_request_initial_fill_quantity_value is not None else None,
        "initial_fill_quantity_comparator": fhir_enum(mr.dispense_request_initial_fill_quantity_comparator) if mr.dispense_request_initial_fill_quantity_comparator else None,
        "initial_fill_quantity_unit": mr.dispense_request_initial_fill_quantity_unit,
        "initial_fill_quantity_system": mr.dispense_request_initial_fill_quantity_system,
        "initial_fill_quantity_code": mr.dispense_request_initial_fill_quantity_code,
        "initial_fill_duration_value": float(mr.dispense_request_initial_fill_duration_value) if mr.dispense_request_initial_fill_duration_value is not None else None,
        "initial_fill_duration_unit": mr.dispense_request_initial_fill_duration_unit,
        "initial_fill_duration_system": mr.dispense_request_initial_fill_duration_system,
        "initial_fill_duration_code": mr.dispense_request_initial_fill_duration_code,
        "dispense_interval_value": float(mr.dispense_request_dispense_interval_value) if mr.dispense_request_dispense_interval_value is not None else None,
        "dispense_interval_unit": mr.dispense_request_dispense_interval_unit,
        "dispense_interval_system": mr.dispense_request_dispense_interval_system,
        "dispense_interval_code": mr.dispense_request_dispense_interval_code,
        "validity_period_start": mr.dispense_request_validity_period_start.isoformat() if mr.dispense_request_validity_period_start else None,
        "validity_period_end": mr.dispense_request_validity_period_end.isoformat() if mr.dispense_request_validity_period_end else None,
        "number_of_repeats_allowed": mr.dispense_request_number_of_repeats_allowed,
        "quantity_value": float(mr.dispense_request_quantity_value) if mr.dispense_request_quantity_value is not None else None,
        "quantity_unit": mr.dispense_request_quantity_unit,
        "quantity_system": mr.dispense_request_quantity_system,
        "quantity_code": mr.dispense_request_quantity_code,
        "expected_supply_duration_value": float(mr.dispense_request_expected_supply_duration_value) if mr.dispense_request_expected_supply_duration_value is not None else None,
        "expected_supply_duration_unit": mr.dispense_request_expected_supply_duration_unit,
        "expected_supply_duration_system": mr.dispense_request_expected_supply_duration_system,
        "expected_supply_duration_code": mr.dispense_request_expected_supply_duration_code,
        "performer": performer,
    }
    if not any(v is not None for v in result.values()):
        return None
    return result


def _plain_substitution(mr: MedicationRequestModel) -> dict | None:
    allowed_cc = _plain_codeable_concept(mr.substitution_allowed_codings, mr.substitution_allowed_codeable_concept_text)
    reason = _plain_codeable_concept(mr.substitution_reason_codings, mr.substitution_reason_text)
    if mr.substitution_allowed_boolean is None and not allowed_cc and not reason:
        return None
    return {
        "allowed_boolean": mr.substitution_allowed_boolean,
        "allowed_codeable_concept": allowed_cc,
        "reason": reason,
    }


def to_plain_medication_request(mr: MedicationRequestModel) -> dict:
    result = {
        "id": mr.medication_request_id,
        "extension": list(mr.extension) if mr.extension else None,
        "identifier": [
            {**(_plain_identifier(i) or {}), "id": i.id} for i in (mr.identifiers or [])
        ]
        or None,
        "status": fhir_enum(mr.status).replace("_", "-") if mr.status else None,
        "status_reason": _plain_codeable_concept(mr.status_reason_codings, mr.status_reason_text),
        "intent": fhir_enum(mr.intent).replace("_", "-") if mr.intent else None,
        "category": [
            {**(_plain_codeable_concept(c.codings, c.text) or {}), "id": c.id} for c in (mr.categories or [])
        ]
        or None,
        "priority": fhir_enum(mr.priority) if mr.priority else None,
        "do_not_perform": mr.do_not_perform,
        "reported_boolean": mr.reported_boolean,
        "reported_reference": _plain_reference(mr, "reported_reference"),
        "medication_codeable_concept": _plain_codeable_concept(mr.medication_codings, mr.medication_codeable_concept_text),
        "medication_reference": _plain_reference(mr, "medication_reference"),
        "subject": _plain_reference(mr, "subject"),
        "encounter": _plain_reference(mr, "encounter"),
        "supporting_information": [_plain_reference_row(si, si.id) for si in (mr.supporting_informations or [])] or None,
        "authored_on": mr.authored_on.isoformat() if mr.authored_on else None,
        "requester": _plain_reference(mr, "requester"),
        "performer": _plain_reference(mr, "performer"),
        "performer_type": _plain_codeable_concept(mr.performer_type_codings, mr.performer_type_text),
        "recorder": _plain_reference(mr, "recorder"),
        "reason_code": [
            {**(_plain_codeable_concept(rc.codings, rc.text) or {}), "id": rc.id} for rc in (mr.reason_codes or [])
        ]
        or None,
        "reason_reference": [_plain_reference_row(rr, rr.id) for rr in (mr.reason_references or [])] or None,
        "instantiates_canonical": list(mr.instantiates_canonical) if mr.instantiates_canonical else None,
        "instantiates_uri": list(mr.instantiates_uri) if mr.instantiates_uri else None,
        "based_on": [_plain_reference_row(b, b.id) for b in (mr.based_ons or [])] or None,
        "group_identifier": _plain_identifier(mr, "group_identifier_"),
        "course_of_therapy_type": _plain_codeable_concept(mr.course_of_therapy_type_codings, mr.course_of_therapy_type_text),
        "insurance": [_plain_reference_row(ins, ins.id) for ins in (mr.insurances or [])] or None,
        "note": [_plain_note(n) for n in (mr.notes or [])] or None,
        "dosage_instruction": [_plain_dosage_instruction(d) for d in (mr.dosage_instructions or [])] or None,
        "dispense_request": _plain_dispense_request(mr),
        "substitution": _plain_substitution(mr),
        "prior_prescription": _plain_reference(mr, "prior_prescription"),
        "detected_issue": [_plain_reference_row(di, di.id) for di in (mr.detected_issues or [])] or None,
        "event_history": [_plain_reference_row(eh, eh.id) for eh in (mr.event_histories or [])] or None,
        "user_id": mr.user_id,
        "org_id": mr.tenant_id,
        "created_at": mr.created_at.isoformat() if mr.created_at else None,
        "updated_at": mr.updated_at.isoformat() if mr.updated_at else None,
        "created_by": mr.created_by,
        "updated_by": mr.updated_by,
    }
    return {k: v for k, v in result.items() if v is not None}
