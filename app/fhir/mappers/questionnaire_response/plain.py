from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.questionnaire_response import (
        QuestionnaireResponseAnswer,
        QuestionnaireResponseItem,
        QuestionnaireResponseModel,
    )


def _plain_reference(obj, prefix: str) -> dict | None:
    """Plain (snake_case) rendering of a `{prefix}_*` flattened Reference
    group — no identifier-fallback detail in the plain form, same
    convention as app.schemas.appointment.response's own actor_*/
    reference_* plain rows."""
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


def plain_questionnaire_response_identifier(qr: QuestionnaireResponseModel) -> dict | None:
    if not (
        qr.identifier_use
        or qr.identifier_type_text
        or qr.identifier_system
        or qr.identifier_value
        or qr.identifier_type_codings
        or qr.identifier_assigner_reference
        or qr.identifier_assigner_id
    ):
        return None
    return {
        "use": fhir_enum(qr.identifier_use) if qr.identifier_use else None,
        "type_codings": [
            {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "user_selected": c.user_selected,
            }
            for c in (qr.identifier_type_codings or [])
        ]
        or None,
        "type_text": qr.identifier_type_text,
        "system": qr.identifier_system,
        "value": qr.identifier_value,
        "period_start": qr.identifier_period_start.isoformat() if qr.identifier_period_start else None,
        "period_end": qr.identifier_period_end.isoformat() if qr.identifier_period_end else None,
        "assigner": qr.identifier_assigner_reference
        or (
            f"{fhir_enum(qr.identifier_assigner_type)}/{qr.identifier_assigner_id}"
            if qr.identifier_assigner_type and qr.identifier_assigner_id
            else None
        ),
        "assigner_id": qr.identifier_assigner_id,
        "assigner_display": qr.identifier_assigner_display,
        "assigner_identifier_use": fhir_enum(qr.identifier_assigner_identifier_use)
        if qr.identifier_assigner_identifier_use
        else None,
        "assigner_identifier_type_system": qr.identifier_assigner_identifier_type_system,
        "assigner_identifier_type_version": qr.identifier_assigner_identifier_type_version,
        "assigner_identifier_type_code": qr.identifier_assigner_identifier_type_code,
        "assigner_identifier_type_display": qr.identifier_assigner_identifier_type_display,
        "assigner_identifier_type_text": qr.identifier_assigner_identifier_type_text,
        "assigner_identifier_type_user_selected": qr.identifier_assigner_identifier_type_user_selected,
        "assigner_identifier_system": qr.identifier_assigner_identifier_system,
        "assigner_identifier_value": qr.identifier_assigner_identifier_value,
        "assigner_identifier_period_start": qr.identifier_assigner_identifier_period_start.isoformat()
        if qr.identifier_assigner_identifier_period_start
        else None,
        "assigner_identifier_period_end": qr.identifier_assigner_identifier_period_end.isoformat()
        if qr.identifier_assigner_identifier_period_end
        else None,
    }


def plain_questionnaire_response_based_on(b) -> dict:
    return {
        "id": b.id,
        "reference": b.reference_reference,
        "reference_type": fhir_enum(b.reference_type) if b.reference_type else None,
        "reference_id": b.reference_id,
        "reference_display": b.reference_display,
    }


def plain_questionnaire_response_part_of(p) -> dict:
    return {
        "id": p.id,
        "reference": p.reference_reference,
        "reference_type": fhir_enum(p.reference_type) if p.reference_type else None,
        "reference_id": p.reference_id,
        "reference_display": p.reference_display,
    }


def _plain_answer_value(a: QuestionnaireResponseAnswer) -> dict:
    return {
        "id": a.id,
        "value_boolean": a.value_boolean,
        "value_decimal": float(a.value_decimal) if a.value_decimal is not None else None,
        "value_integer": a.value_integer,
        "value_date": a.value_date.isoformat() if a.value_date else None,
        "value_date_time": a.value_date_time.isoformat() if a.value_date_time else None,
        "value_time": a.value_time.isoformat() if a.value_time else None,
        "value_string": a.value_string,
        "value_uri": a.value_uri,
        "value_attachment": {
            "content_type": a.content_type,
            "language": a.language,
            "data": a.data,
            "url": a.url,
            "size": a.size,
            "hash": a.hash,
            "title": a.title,
            "creation": a.creation.isoformat() if a.creation else None,
        }
        if (a.content_type or a.url or a.data or a.title)
        else None,
        "value_coding_system": a.system,
        "value_coding_version": a.version,
        "value_coding_code": a.code,
        "value_coding_display": a.display,
        "value_coding_user_selected": a.user_selected,
        "value_quantity_value": float(a.value_quantity_value) if a.value_quantity_value is not None else None,
        "value_quantity_comparator": fhir_enum(a.value_quantity_comparator) if a.value_quantity_comparator else None,
        "value_quantity_unit": a.value_quantity_unit,
        "value_quantity_system": a.value_quantity_system,
        "value_quantity_code": a.value_quantity_code,
        "value_reference": a.value_reference_reference,
        "value_reference_type": a.value_reference_type,
        "value_reference_id": a.value_reference_id,
        "value_reference_display": a.value_reference_display,
    }


def _build_plain_item_tree(
    items: list[QuestionnaireResponseItem], answers: list[QuestionnaireResponseAnswer]
) -> list[dict]:
    """Plain-JSON counterpart of
    app.fhir.mappers.questionnaire_response.fhir._build_response_item_tree
    — same grouping, snake_case output."""
    items_by_parent_item: dict[int | None, list] = {}
    items_by_parent_answer: dict[int, list] = {}
    for item in items:
        if item.parent_answer_id is not None:
            items_by_parent_answer.setdefault(item.parent_answer_id, []).append(item)
        else:
            items_by_parent_item.setdefault(item.parent_item_id, []).append(item)

    answers_by_item: dict[int, list] = {}
    for answer in answers:
        answers_by_item.setdefault(answer.item_id, []).append(answer)

    def render_answer(answer: QuestionnaireResponseAnswer) -> dict:
        entry = _plain_answer_value(answer)
        children = render_items(items_by_parent_answer.get(answer.id, []))
        entry["item"] = children or None
        return entry

    def render_items(item_list: list) -> list[dict]:
        result = []
        for item in item_list:
            answer_entries = [render_answer(a) for a in answers_by_item.get(item.id, [])]
            entry = {
                "id": item.id,
                "link_id": item.link_id,
                "definition": item.definition,
                "text": item.text,
                "answer": answer_entries or None,
                "item": render_items(items_by_parent_item.get(item.id, [])) or None,
            }
            result.append(entry)
        return result

    return render_items(items_by_parent_item.get(None, []))


def to_plain_questionnaire_response(qr: QuestionnaireResponseModel) -> dict:
    subject = _plain_reference(qr, "subject")
    encounter = _plain_reference(qr, "encounter")
    author = _plain_reference(qr, "author")
    source = _plain_reference(qr, "source")

    result = {
        "id": qr.questionnaire_response_id,
        "extension": list(qr.extension) if qr.extension else None,
        "identifier": plain_questionnaire_response_identifier(qr),
        "based_on": [plain_questionnaire_response_based_on(b) for b in (qr.based_ons or [])] or None,
        "part_of": [plain_questionnaire_response_part_of(p) for p in (qr.part_ofs or [])] or None,
        "questionnaire": qr.questionnaire,
        "status": fhir_enum(qr.status).replace("_", "-") if qr.status else None,
        "subject": subject,
        "encounter": encounter,
        "authored": qr.authored.isoformat() if qr.authored else None,
        "author": author,
        "source": source,
        "item": _build_plain_item_tree(qr.items or [], qr.answers or []) or None,
        "org_id": qr.tenant_id,
        "created_at": qr.created_at.isoformat() if qr.created_at else None,
        "updated_at": qr.updated_at.isoformat() if qr.updated_at else None,
        "created_by": qr.created_by,
        "updated_by": qr.updated_by,
    }
    return {k: v for k, v in result.items() if v is not None}
