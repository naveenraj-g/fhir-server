from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.goal import (
        GoalCategory,
        GoalIdentifier,
        GoalModel,
        GoalNote,
        GoalOutcomeCode,
        GoalTarget,
    )


def _format_date(d) -> str | None:
    if not d:
        return None
    return d.isoformat() if hasattr(d, "isoformat") else str(d)


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


def _plain_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _plain_coding_list(codings)
    if not coding_list and not text:
        return None
    result: dict[str, Any] = {}
    if text:
        result["text"] = text
    if coding_list:
        result["codings"] = coding_list
    return result


def _plain_ref_str(
    ref_raw: str | None,
    ref_type: Any,
    ref_id: int | None,
) -> str | None:
    if ref_raw:
        return ref_raw
    if ref_type and ref_id:
        return f"{fhir_enum(ref_type)}/{ref_id}"
    return None


def _plain_reference_row(row) -> dict:
    computed = _plain_ref_str(
        row.reference_reference, row.reference_type, row.reference_id
    )
    return {
        "id": row.id,
        "reference_reference": row.reference_reference,
        "reference": computed,
        "reference_type": fhir_enum(row.reference_type),
        "reference_id": row.reference_id,
        "reference_display": row.reference_display,
        "created_at": fhir_instant(row.created_at) if hasattr(row, "created_at") else None,
        "updated_at": fhir_instant(row.updated_at) if hasattr(row, "updated_at") else None,
        "created_by": getattr(row, "created_by", None),
        "updated_by": getattr(row, "updated_by", None),
        "tenant_id": getattr(row, "tenant_id", None),
    }


def _plain_identifier(i: GoalIdentifier) -> dict:
    computed_assigner = _plain_ref_str(
        i.assigner_reference, i.assigner_type, i.assigner_id
    )
    return {
        "id": i.id,
        "use": fhir_enum(i.use),
        "type_text": i.type_text,
        "type_codings": _plain_coding_list(getattr(i, "codings", None)),
        "system": i.system,
        "value": i.value,
        "period_start": fhir_instant(i.period_start) if i.period_start else None,
        "period_end": fhir_instant(i.period_end) if i.period_end else None,
        "assigner_reference": i.assigner_reference,
        "assigner": computed_assigner,
        "assigner_type": fhir_enum(i.assigner_type),
        "assigner_id": i.assigner_id,
        "assigner_display": i.assigner_display,
        "created_at": fhir_instant(i.created_at) if hasattr(i, "created_at") else None,
        "updated_at": fhir_instant(i.updated_at) if hasattr(i, "updated_at") else None,
        "created_by": getattr(i, "created_by", None),
        "updated_by": getattr(i, "updated_by", None),
        "tenant_id": getattr(i, "tenant_id", None),
    }


def _plain_category(c: GoalCategory | GoalOutcomeCode) -> dict:
    return {
        "id": c.id,
        "text": c.text,
        "codings": _plain_coding_list(getattr(c, "codings", None)),
        "created_at": fhir_instant(c.created_at) if hasattr(c, "created_at") else None,
        "updated_at": fhir_instant(c.updated_at) if hasattr(c, "updated_at") else None,
        "created_by": getattr(c, "created_by", None),
        "updated_by": getattr(c, "updated_by", None),
        "tenant_id": getattr(c, "tenant_id", None),
    }


def _plain_note(n: GoalNote) -> dict:
    computed_author = _plain_ref_str(
        n.author_reference, n.author_type, n.author_id
    )
    return {
        "id": n.id,
        "author_string": n.author_string,
        "author_reference": n.author_reference,
        "author": computed_author,
        "author_type": fhir_enum(n.author_type),
        "author_id": n.author_id,
        "author_display": n.author_display,
        "time": fhir_instant(n.time) if n.time else None,
        "text": n.text,
        "created_at": fhir_instant(n.created_at) if hasattr(n, "created_at") else None,
        "updated_at": fhir_instant(n.updated_at) if hasattr(n, "updated_at") else None,
        "created_by": getattr(n, "created_by", None),
        "updated_by": getattr(n, "updated_by", None),
        "tenant_id": getattr(n, "tenant_id", None),
    }


def _plain_target(t: GoalTarget) -> dict:
    return {
        "id": t.id,
        "measure_text": t.measure_text,
        "measure_codings": _plain_coding_list(getattr(t, "measure_codings", None)),
        "detail_string": t.detail_string,
        "detail_boolean": t.detail_boolean,
        "detail_integer": t.detail_integer,
        "detail_quantity_value": float(t.detail_quantity_value) if t.detail_quantity_value is not None else None,
        "detail_quantity_unit": t.detail_quantity_unit,
        "detail_quantity_system": t.detail_quantity_system,
        "detail_quantity_code": t.detail_quantity_code,
        "detail_quantity_comparator": t.detail_quantity_comparator,
        "detail_range_low_value": float(t.detail_range_low_value) if t.detail_range_low_value is not None else None,
        "detail_range_low_unit": t.detail_range_low_unit,
        "detail_range_low_system": t.detail_range_low_system,
        "detail_range_low_code": t.detail_range_low_code,
        "detail_range_high_value": float(t.detail_range_high_value) if t.detail_range_high_value is not None else None,
        "detail_range_high_unit": t.detail_range_high_unit,
        "detail_range_high_system": t.detail_range_high_system,
        "detail_range_high_code": t.detail_range_high_code,
        "detail_ratio_numerator_value": float(t.detail_ratio_numerator_value) if t.detail_ratio_numerator_value is not None else None,
        "detail_ratio_numerator_unit": t.detail_ratio_numerator_unit,
        "detail_ratio_numerator_system": t.detail_ratio_numerator_system,
        "detail_ratio_numerator_code": t.detail_ratio_numerator_code,
        "detail_ratio_denominator_value": float(t.detail_ratio_denominator_value) if t.detail_ratio_denominator_value is not None else None,
        "detail_ratio_denominator_unit": t.detail_ratio_denominator_unit,
        "detail_ratio_denominator_system": t.detail_ratio_denominator_system,
        "detail_ratio_denominator_code": t.detail_ratio_denominator_code,
        "detail_codeable_concept_text": t.detail_codeable_concept_text,
        "detail_codings": _plain_coding_list(getattr(t, "detail_codings", None)),
        "due_date": _format_date(t.due_date),
        "due_duration_value": float(t.due_duration_value) if t.due_duration_value is not None else None,
        "due_duration_unit": t.due_duration_unit,
        "due_duration_system": t.due_duration_system,
        "due_duration_code": t.due_duration_code,
        "created_at": fhir_instant(t.created_at) if hasattr(t, "created_at") else None,
        "updated_at": fhir_instant(t.updated_at) if hasattr(t, "updated_at") else None,
        "created_by": getattr(t, "created_by", None),
        "updated_by": getattr(t, "updated_by", None),
        "tenant_id": getattr(t, "tenant_id", None),
    }


def to_plain_goal(model: GoalModel) -> dict:
    """Serialize GoalModel to a plain snake_case dict."""
    computed_subject = _plain_ref_str(
        model.subject_reference, model.subject_type, model.subject_id
    ) or ""
    computed_expressed_by = _plain_ref_str(
        model.expressed_by_reference,
        model.expressed_by_type,
        model.expressed_by_id,
    )

    return {
        "id": model.goal_id,
        "lifecycle_status": fhir_enum(model.lifecycle_status),
        "achievement_status": _plain_codeable_concept(
            model.achievement_status_codings, model.achievement_status_text
        ),
        "category": [
            _plain_category(c) for c in (model.categories or [])
        ],
        "priority": _plain_codeable_concept(
            model.priority_codings, model.priority_text
        ),
        "description": _plain_codeable_concept(
            model.description_codings, model.description_text
        ),
        "subject": computed_subject,
        "subject_display": model.subject_display,
        "subject_type": fhir_enum(model.subject_type),
        "subject_id": model.subject_id,
        "start_date": _format_date(model.start_date),
        "start_codeable_concept": _plain_codeable_concept(
            model.start_codings, model.start_codeable_concept_text
        ),
        "target": [_plain_target(t) for t in (model.targets or [])],
        "status_date": _format_date(model.status_date),
        "status_reason": model.status_reason,
        "expressed_by": computed_expressed_by,
        "expressed_by_display": model.expressed_by_display,
        "expressed_by_type": fhir_enum(model.expressed_by_type),
        "expressed_by_id": model.expressed_by_id,
        "addresses": [
            _plain_reference_row(a) for a in (model.addresses_list or [])
        ],
        "note": [_plain_note(n) for n in (model.notes or [])],
        "outcome_code": [
            _plain_category(oc) for oc in (model.outcome_codes or [])
        ],
        "outcome_reference": [
            _plain_reference_row(o) for o in (model.outcome_references or [])
        ],
        "identifier": [
            _plain_identifier(i) for i in (model.identifiers or [])
        ],
        "extension": model.extension or [],
        "created_at": fhir_instant(model.created_at),
        "updated_at": fhir_instant(model.updated_at),
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "tenant_id": model.tenant_id,
    }
