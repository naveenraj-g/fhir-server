from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.communication import (
        CommunicationIdentifier,
        CommunicationModel,
        CommunicationNote,
        CommunicationPayload,
    )


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


def _plain_identifier(i: CommunicationIdentifier) -> dict:
    computed_assigner = _plain_ref_str(
        i.assigner_reference, i.assigner_type, i.assigner_id
    )
    return {
        "id": i.id,
        "use": fhir_enum(i.use),
        "type_text": i.type_text,
        "type_codings": _plain_coding_list(getattr(i, "type_codings", None)),
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


def _plain_note(n: CommunicationNote) -> dict:
    computed_author = _plain_ref_str(
        n.author_reference, n.author_type, n.author_id
    )
    return {
        "id": n.id,
        "author_string": n.author_string,
        "author_reference": n.author_reference,
        "author": computed_author,
        "author_type": n.author_type,
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


def _plain_payload(p: CommunicationPayload) -> dict:
    computed_ref = _plain_ref_str(
        p.content_reference_reference,
        p.content_reference_type,
        p.content_reference_id,
    )
    att = None
    if (
        p.data
        or p.url
        or p.title
        or p.content_type
    ):
        att = {
            "content_type": p.content_type,
            "language": p.language,
            "data": p.data,
            "url": p.url,
            "size": p.size,
            "hash": p.hash,
            "title": p.title,
            "creation": fhir_instant(p.creation) if p.creation else None,
        }
    return {
        "id": p.id,
        "content_string": p.content_string,
        "content_attachment": att,
        "content_reference_reference": p.content_reference_reference,
        "content_reference": computed_ref,
        "content_reference_type": p.content_reference_type,
        "content_reference_id": p.content_reference_id,
        "content_reference_display": p.content_reference_display,
        "created_at": fhir_instant(p.created_at) if hasattr(p, "created_at") else None,
        "updated_at": fhir_instant(p.updated_at) if hasattr(p, "updated_at") else None,
        "created_by": getattr(p, "created_by", None),
        "updated_by": getattr(p, "updated_by", None),
        "tenant_id": getattr(p, "tenant_id", None),
    }


def to_plain_communication(model: CommunicationModel) -> dict:
    """Map SQLAlchemy CommunicationModel to a plain snake_case dict."""
    subject_str = _plain_ref_str(
        model.subject_reference, model.subject_type, model.subject_id
    )
    encounter_str = _plain_ref_str(
        model.encounter_reference, model.encounter_type, model.encounter_id
    )
    sender_str = _plain_ref_str(
        model.sender_reference, model.sender_type, model.sender_id
    )

    result: dict[str, Any] = {
        "id": model.communication_id,
        "instantiates_canonical": list(model.instantiates_canonical) if model.instantiates_canonical else None,
        "instantiates_uri": list(model.instantiates_uri) if model.instantiates_uri else None,
        "status": fhir_enum(model.status),
        "status_reason_text": model.status_reason_text,
        "status_reason_codings": _plain_coding_list(model.status_reason_codings) if model.status_reason_codings else None,
        "priority": fhir_enum(model.priority),
        "subject_reference": model.subject_reference,
        "subject": subject_str,
        "subject_type": fhir_enum(model.subject_type),
        "subject_id": model.subject_id,
        "subject_display": model.subject_display,
        "topic_text": model.topic_text,
        "topic_codings": _plain_coding_list(model.topic_codings) if model.topic_codings else None,
        "encounter_reference": model.encounter_reference,
        "encounter": encounter_str,
        "encounter_type": fhir_enum(model.encounter_type),
        "encounter_id": model.encounter_id,
        "encounter_display": model.encounter_display,
        "sent": fhir_instant(model.sent) if model.sent else None,
        "received": fhir_instant(model.received) if model.received else None,
        "sender_reference": model.sender_reference,
        "sender": sender_str,
        "sender_type": fhir_enum(model.sender_type),
        "sender_id": model.sender_id,
        "sender_display": model.sender_display,
        "created_at": fhir_instant(model.created_at) if hasattr(model, "created_at") else None,
        "updated_at": fhir_instant(model.updated_at) if hasattr(model, "updated_at") else None,
        "created_by": getattr(model, "created_by", None),
        "updated_by": getattr(model, "updated_by", None),
        "tenant_id": getattr(model, "tenant_id", None),
    }

    if model.identifiers:
        result["identifier"] = [_plain_identifier(i) for i in model.identifiers]

    if model.based_on_list:
        result["based_on"] = [_plain_reference_row(b) for b in model.based_on_list]

    if model.part_of_list:
        result["part_of"] = [_plain_reference_row(p) for p in model.part_of_list]

    if model.in_response_to_list:
        result["in_response_to"] = [_plain_reference_row(r) for r in model.in_response_to_list]

    if model.categories:
        result["category"] = [
            {"id": c.id, "text": c.text, "codings": _plain_coding_list(c.codings)}
            for c in model.categories
        ]

    if model.medium_list:
        result["medium"] = [
            {"id": m.id, "text": m.text, "codings": _plain_coding_list(m.codings)}
            for m in model.medium_list
        ]

    if model.about_list:
        result["about"] = [_plain_reference_row(a) for a in model.about_list]

    if model.recipients:
        result["recipient"] = [_plain_reference_row(rec) for rec in model.recipients]

    if model.reason_codes:
        result["reason_code"] = [
            {"id": rc.id, "text": rc.text, "codings": _plain_coding_list(rc.codings)}
            for rc in model.reason_codes
        ]

    if model.reason_references:
        result["reason_reference"] = [_plain_reference_row(rr) for rr in model.reason_references]

    if model.payloads:
        result["payload"] = [_plain_payload(p) for p in model.payloads]

    if model.notes:
        result["note"] = [_plain_note(n) for n in model.notes]

    if model.extension:
        result["extension"] = model.extension

    return result
