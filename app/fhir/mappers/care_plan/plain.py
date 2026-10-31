from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.care_plan import CarePlanActivity, CarePlanModel


def _plain_coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            "id": c.id,
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
        }
        result.append(entry)
    return result


def _plain_identifier(i) -> dict:
    return {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type_text": i.type_text,
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start.isoformat() if i.period_start else None,
        "period_end": i.period_end.isoformat() if i.period_end else None,
        "assigner_reference": i.assigner_reference,
        "assigner_type": fhir_enum(i.assigner_type) if i.assigner_type else None,
        "assigner_id": i.assigner_id,
        "assigner_display": i.assigner_display,
        "type_codings": _plain_coding_list(getattr(i, "type_codings", None)),
    }


def _plain_category(c) -> dict:
    return {
        "id": c.id,
        "text": c.text,
        "codings": _plain_coding_list(getattr(c, "codings", None)),
    }


def _plain_ref_row(r) -> dict:
    return {
        "id": r.id,
        "reference": r.reference_reference,
        "type": fhir_enum(r.reference_type) if r.reference_type else None,
        "reference_id": r.reference_id,
        "display": r.reference_display,
    }


def _plain_note(n) -> dict:
    return {
        "id": n.id,
        "text": n.text,
        "time": n.time.isoformat() if n.time else None,
        "author_string": n.author_string,
        "author_reference": n.author_reference_reference,
        "author_type": fhir_enum(n.author_reference_type) if n.author_reference_type else None,
        "author_id": n.author_reference_id,
        "author_display": n.author_reference_display,
    }


def _plain_activity_detail(act: CarePlanActivity) -> dict | None:
    has_any = (
        act.detail_kind is not None
        or act.detail_instantiates_canonical
        or act.detail_instantiates_uri
        or act.detail_code_text
        or getattr(act, "detail_code_codings", None)
        or act.detail_status is not None
        or act.detail_status_reason_text
        or getattr(act, "detail_status_reason_codings", None)
        or act.detail_do_not_perform is not None
        or act.detail_scheduled_timing
        or act.detail_scheduled_period_start
        or act.detail_scheduled_period_end
        or act.detail_scheduled_string
        or act.detail_location_reference
        or act.detail_location_type
        or act.detail_location_id
        or act.detail_location_display
        or getattr(act, "detail_performers", None)
        or act.detail_product_codeable_concept_text
        or getattr(act, "detail_product_codings", None)
        or act.detail_product_reference
        or act.detail_product_type
        or act.detail_product_id
        or act.detail_product_display
        or act.detail_daily_amount_value is not None
        or act.detail_quantity_value is not None
        or act.detail_description
        or getattr(act, "detail_reason_codes", None)
        or getattr(act, "detail_reason_references", None)
        or getattr(act, "detail_goals", None)
    )
    if not has_any:
        return None

    detail: dict[str, Any] = {
        "kind": fhir_enum(act.detail_kind) if act.detail_kind else None,
        "instantiates_canonical": list(act.detail_instantiates_canonical) if act.detail_instantiates_canonical else None,
        "instantiates_uri": list(act.detail_instantiates_uri) if act.detail_instantiates_uri else None,
        "code_text": act.detail_code_text,
        "code_codings": _plain_coding_list(getattr(act, "detail_code_codings", None)),
        "reason_codes": [
            {"id": rc.id, "text": rc.text, "codings": _plain_coding_list(getattr(rc, "codings", None))}
            for rc in (getattr(act, "detail_reason_codes", None) or [])
        ],
        "reason_references": [
            _plain_ref_row(rr) for rr in (getattr(act, "detail_reason_references", None) or [])
        ],
        "goals": [
            _plain_ref_row(g) for g in (getattr(act, "detail_goals", None) or [])
        ],
        "status": fhir_enum(act.detail_status) if act.detail_status else None,
        "status_reason_text": act.detail_status_reason_text,
        "status_reason_codings": _plain_coding_list(getattr(act, "detail_status_reason_codings", None)),
        "do_not_perform": act.detail_do_not_perform,
        "scheduled_timing": act.detail_scheduled_timing,
        "scheduled_period_start": act.detail_scheduled_period_start.isoformat() if act.detail_scheduled_period_start else None,
        "scheduled_period_end": act.detail_scheduled_period_end.isoformat() if act.detail_scheduled_period_end else None,
        "scheduled_string": act.detail_scheduled_string,
        "location_id": act.detail_location_id,
        "location_type": fhir_enum(act.detail_location_type) if act.detail_location_type else None,
        "location_reference": act.detail_location_reference,
        "location_display": act.detail_location_display,
        "performers": [
            _plain_ref_row(p) for p in (getattr(act, "detail_performers", None) or [])
        ],
        "product_codeable_concept_text": act.detail_product_codeable_concept_text,
        "product_codings": _plain_coding_list(getattr(act, "detail_product_codings", None)),
        "product_id": act.detail_product_id,
        "product_type": fhir_enum(act.detail_product_type) if act.detail_product_type else None,
        "product_reference": act.detail_product_reference,
        "product_display": act.detail_product_display,
        "daily_amount_value": float(act.detail_daily_amount_value) if act.detail_daily_amount_value is not None else None,
        "daily_amount_comparator": fhir_enum(act.detail_daily_amount_comparator) if act.detail_daily_amount_comparator else None,
        "daily_amount_unit": act.detail_daily_amount_unit,
        "daily_amount_system": act.detail_daily_amount_system,
        "daily_amount_code": act.detail_daily_amount_code,
        "quantity_value": float(act.detail_quantity_value) if act.detail_quantity_value is not None else None,
        "quantity_comparator": fhir_enum(act.detail_quantity_comparator) if act.detail_quantity_comparator else None,
        "quantity_unit": act.detail_quantity_unit,
        "quantity_system": act.detail_quantity_system,
        "quantity_code": act.detail_quantity_code,
        "description": act.detail_description,
    }
    return detail


def _plain_activity(act: CarePlanActivity) -> dict:
    return {
        "id": act.id,
        "reference_id": act.reference_id,
        "reference_type": fhir_enum(act.reference_type) if act.reference_type else None,
        "reference_reference": act.reference_reference,
        "reference_display": act.reference_display,
        "outcome_codeable_concepts": [
            {"id": occ.id, "text": occ.text, "codings": _plain_coding_list(getattr(occ, "codings", None))}
            for occ in (getattr(act, "outcome_codeable_concepts", None) or [])
        ],
        "outcome_references": [
            _plain_ref_row(oref) for oref in (getattr(act, "outcome_references", None) or [])
        ],
        "progress": [_plain_note(p) for p in (getattr(act, "progress", None) or [])],
        "detail": _plain_activity_detail(act),
    }


def to_plain_care_plan(model: CarePlanModel) -> dict:
    """Transform CarePlanModel into plain snake_case representation."""
    return {
        "id": model.care_plan_id,
        "instantiates_canonical": list(model.instantiates_canonical) if model.instantiates_canonical else None,
        "instantiates_uri": list(model.instantiates_uri) if model.instantiates_uri else None,
        "status": fhir_enum(model.status),
        "intent": fhir_enum(model.intent),
        "title": model.title,
        "description": model.description,
        "subject": model.subject_reference or (f"{fhir_enum(model.subject_type)}/{model.subject_id}" if model.subject_type and model.subject_id else None),
        "subject_id": model.subject_id,
        "subject_type": fhir_enum(model.subject_type) if model.subject_type else None,
        "subject_display": model.subject_display,
        "encounter": model.encounter_reference or (f"{fhir_enum(model.encounter_type)}/{model.encounter_id}" if model.encounter_type and model.encounter_id else None),
        "encounter_id": model.encounter_id,
        "encounter_type": fhir_enum(model.encounter_type) if model.encounter_type else None,
        "encounter_display": model.encounter_display,
        "period_start": model.period_start.isoformat() if model.period_start else None,
        "period_end": model.period_end.isoformat() if model.period_end else None,
        "created": model.created.isoformat() if model.created else None,
        "author": model.author_reference or (f"{fhir_enum(model.author_type)}/{model.author_id}" if model.author_type and model.author_id else None),
        "author_id": model.author_id,
        "author_type": fhir_enum(model.author_type) if model.author_type else None,
        "author_display": model.author_display,
        "identifiers": [_plain_identifier(i) for i in (getattr(model, "identifiers", None) or [])],
        "categories": [_plain_category(c) for c in (getattr(model, "categories", None) or [])],
        "based_on": [_plain_ref_row(b) for b in (getattr(model, "based_on", None) or [])],
        "replaces": [_plain_ref_row(r) for r in (getattr(model, "replaces", None) or [])],
        "part_of": [_plain_ref_row(p) for p in (getattr(model, "part_of", None) or [])],
        "contributors": [_plain_ref_row(c) for c in (getattr(model, "contributors", None) or [])],
        "care_teams": [_plain_ref_row(ct) for ct in (getattr(model, "care_teams", None) or [])],
        "addresses": [_plain_ref_row(a) for a in (getattr(model, "addresses", None) or [])],
        "goals": [_plain_ref_row(g) for g in (getattr(model, "goals", None) or [])],
        "activities": [_plain_activity(a) for a in (getattr(model, "activities", None) or [])],
        "notes": [_plain_note(n) for n in (getattr(model, "notes", None) or [])],
        "tenant_id": model.tenant_id,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }
