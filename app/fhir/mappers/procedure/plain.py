from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.procedure import (
        ProcedureFocalDevice,
        ProcedureIdentifier,
        ProcedureModel,
        ProcedureNote,
        ProcedurePerformer,
    )


def _plain_ref(ref_raw: str | None, ref_type: Any, ref_id: int | None) -> str | None:
    if ref_raw:
        return ref_raw
    if ref_type and ref_id:
        return f"{fhir_enum(ref_type)}/{ref_id}"
    return None


def _plain_single_concept(codings, text: str | None) -> dict | None:
    c_list = [
        {
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
        }
        for c in codings or []
    ]
    if not c_list and not text:
        return None
    res: dict = {}
    if text:
        res["text"] = text
    if c_list:
        res["codings"] = c_list
    return res


def _plain_concept_row(concept) -> dict:
    codings = [
        {
            "id": c.id,
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
        }
        for c in getattr(concept, "codings", []) or []
    ]
    return {
        "id": concept.id,
        "text": concept.text,
        "codings": codings or None,
    }


def _plain_identifier(i: ProcedureIdentifier) -> dict:
    type_obj = None
    if i.type_text or getattr(i, "type_codings", None):
        type_obj = {
            "text": i.type_text,
            "coding": [
                {
                    "system": c.system,
                    "version": c.version,
                    "code": c.code,
                    "display": c.display,
                    "user_selected": c.user_selected,
                }
                for c in getattr(i, "type_codings", []) or []
            ]
            or None,
        }
    return {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type": type_obj,
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start,
        "period_end": i.period_end,
        "assigner": _plain_ref(i.assigner_reference, i.assigner_type, i.assigner_id),
        "assigner_display": i.assigner_display,
    }


def _plain_performer(p: ProcedurePerformer) -> dict:
    return {
        "id": p.id,
        "function": _plain_single_concept(getattr(p, "function_codings", None), p.function_text),
        "actor": _plain_ref(p.actor_reference, p.actor_type, p.actor_id),
        "actor_display": p.actor_display,
        "on_behalf_of": _plain_ref(p.on_behalf_of_reference, p.on_behalf_of_type, p.on_behalf_of_id),
        "on_behalf_of_display": p.on_behalf_of_display,
    }


def _plain_focal_device(d: ProcedureFocalDevice) -> dict:
    return {
        "id": d.id,
        "action": _plain_single_concept(getattr(d, "action_codings", None), d.action_text),
        "manipulated": _plain_ref(d.manipulated_reference, d.manipulated_type, d.manipulated_id),
        "manipulated_display": d.manipulated_display,
    }


def _plain_note(n: ProcedureNote) -> dict:
    return {
        "id": n.id,
        "author_string": n.author_string,
        "author_reference": _plain_ref(
            getattr(n, "author_reference_reference", None),
            getattr(n, "author_reference_type", None),
            getattr(n, "author_reference_id", None),
        ),
        "author_reference_display": getattr(n, "author_reference_display", None),
        "time": n.time,
        "text": n.text,
    }


def to_plain_procedure(model: ProcedureModel) -> dict:
    """Map ProcedureModel ORM instance to plain snake_case dictionary."""
    based_on = [
        _plain_ref(b.reference_reference, b.reference_type, b.reference_id)
        for b in getattr(model, "based_on", []) or []
    ]
    based_on = [b for b in based_on if b]

    part_of = [
        _plain_ref(p.reference_reference, p.reference_type, p.reference_id)
        for p in getattr(model, "part_of", []) or []
    ]
    part_of = [p for p in part_of if p]

    reason_reference = [
        _plain_ref(rr.reference_reference, rr.reference_type, rr.reference_id)
        for rr in getattr(model, "reason_references", []) or []
    ]
    reason_reference = [rr for rr in reason_reference if rr]

    report = [
        _plain_ref(r.reference_reference, r.reference_type, r.reference_id)
        for r in getattr(model, "reports", []) or []
    ]
    report = [r for r in report if r]

    complication_detail = [
        _plain_ref(cd.reference_reference, cd.reference_type, cd.reference_id)
        for cd in getattr(model, "complication_details", []) or []
    ]
    complication_detail = [cd for cd in complication_detail if cd]

    used_reference = [
        _plain_ref(ur.reference_reference, ur.reference_type, ur.reference_id)
        for ur in getattr(model, "used_references", []) or []
    ]
    used_reference = [ur for ur in used_reference if ur]

    return {
        "id": model.procedure_id,
        "instantiates_canonical": model.instantiates_canonical,
        "instantiates_uri": model.instantiates_uri,
        "based_on": based_on or None,
        "part_of": part_of or None,
        "status": fhir_enum(model.status) if model.status else None,
        "status_reason": _plain_single_concept(
            getattr(model, "status_reason_codings", None),
            model.status_reason_text,
        ),
        "category": _plain_single_concept(
            getattr(model, "category_codings", None),
            model.category_text,
        ),
        "code": _plain_single_concept(
            getattr(model, "code_codings", None),
            model.code_text,
        ),
        "subject": _plain_ref(
            model.subject_reference,
            model.subject_type,
            model.subject_id,
        ),
        "subject_display": model.subject_display,
        "encounter": _plain_ref(
            model.encounter_reference,
            model.encounter_type,
            model.encounter_id,
        ),
        "encounter_display": model.encounter_display,
        "performed_date_time": model.performed_date_time,
        "performed_period_start": model.performed_period_start,
        "performed_period_end": model.performed_period_end,
        "performed_string": model.performed_string,
        "performed_age": model.performed_age,
        "performed_range": model.performed_range,
        "recorder": _plain_ref(
            model.recorder_reference,
            model.recorder_type,
            model.recorder_id,
        ),
        "recorder_display": model.recorder_display,
        "asserter": _plain_ref(
            model.asserter_reference,
            model.asserter_type,
            model.asserter_id,
        ),
        "asserter_display": model.asserter_display,
        "performer": [
            _plain_performer(p) for p in getattr(model, "performers", []) or []
        ]
        or None,
        "location": _plain_ref(
            model.location_reference,
            model.location_type,
            model.location_id,
        ),
        "location_display": model.location_display,
        "reason_code": [
            _plain_concept_row(rc)
            for rc in getattr(model, "reason_codes", []) or []
        ]
        or None,
        "reason_reference": reason_reference or None,
        "body_site": [
            _plain_concept_row(bs)
            for bs in getattr(model, "body_sites", []) or []
        ]
        or None,
        "outcome": _plain_single_concept(
            getattr(model, "outcome_codings", None),
            model.outcome_text,
        ),
        "report": report or None,
        "complication": [
            _plain_concept_row(c)
            for c in getattr(model, "complications", []) or []
        ]
        or None,
        "complication_detail": complication_detail or None,
        "follow_up": [
            _plain_concept_row(fu)
            for fu in getattr(model, "follow_ups", []) or []
        ]
        or None,
        "note": [
            _plain_note(n) for n in getattr(model, "notes", []) or []
        ]
        or None,
        "focal_device": [
            _plain_focal_device(d)
            for d in getattr(model, "focal_devices", []) or []
        ]
        or None,
        "used_reference": used_reference or None,
        "used_code": [
            _plain_concept_row(uc)
            for uc in getattr(model, "used_codes", []) or []
        ]
        or None,
        "identifier": [
            _plain_identifier(i)
            for i in getattr(model, "identifiers", []) or []
        ]
        or None,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
