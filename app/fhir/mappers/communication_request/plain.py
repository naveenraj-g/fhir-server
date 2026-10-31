from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.communication_request import (
        CommunicationRequestIdentifier,
        CommunicationRequestModel,
        CommunicationRequestNote,
        CommunicationRequestPayload,
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


def _plain_identifier(i: CommunicationRequestIdentifier) -> dict:
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


def _plain_note(n: CommunicationRequestNote) -> dict:
    return {
        "id": n.id,
        "author_string": n.author_string,
        "author_reference": n.author_reference,
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


def _plain_payload(p: CommunicationRequestPayload) -> dict:
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
            "creation": fhir_instant(p.creation)
            if p.creation
            else None,
        }
    computed_ref = _plain_ref_str(
        p.content_reference_reference,
        p.content_reference_type,
        p.content_reference_id,
    )
    return {
        "id": p.id,
        "content_string": p.content_string,
        "content_attachment": att,
        "content_reference": computed_ref,
        "content_reference_type": fhir_enum(p.content_reference_type),
        "content_reference_id": p.content_reference_id,
        "content_reference_display": p.content_reference_display,
        "created_at": fhir_instant(p.created_at) if hasattr(p, "created_at") else None,
        "updated_at": fhir_instant(p.updated_at) if hasattr(p, "updated_at") else None,
        "created_by": getattr(p, "created_by", None),
        "updated_by": getattr(p, "updated_by", None),
        "tenant_id": getattr(p, "tenant_id", None),
    }


def to_plain_communication_request(model: CommunicationRequestModel) -> dict:
    """Map SQLAlchemy CommunicationRequestModel to a plain snake_case dictionary."""
    computed_subject = _plain_ref_str(
        model.subject_reference, model.subject_type, model.subject_id
    )
    computed_encounter = _plain_ref_str(
        model.encounter_reference, model.encounter_type, model.encounter_id
    )
    computed_requester = _plain_ref_str(
        model.requester_reference, model.requester_type, model.requester_id
    )
    computed_sender = _plain_ref_str(
        model.sender_reference, model.sender_type, model.sender_id
    )
    computed_group_assigner = _plain_ref_str(
        model.group_identifier_assigner_reference,
        model.group_identifier_assigner_type,
        model.group_identifier_assigner_id,
    )

    result: dict[str, Any] = {
        "id": model.communication_request_id,
        "group_identifier_use": fhir_enum(model.group_identifier_use),
        "group_identifier_system": model.group_identifier_system,
        "group_identifier_value": model.group_identifier_value,
        "group_identifier_period_start": fhir_instant(model.group_identifier_period_start)
        if model.group_identifier_period_start
        else None,
        "group_identifier_period_end": fhir_instant(model.group_identifier_period_end)
        if model.group_identifier_period_end
        else None,
        "group_identifier_assigner_reference": model.group_identifier_assigner_reference,
        "group_identifier_assigner": computed_group_assigner,
        "group_identifier_assigner_type": fhir_enum(model.group_identifier_assigner_type),
        "group_identifier_assigner_id": model.group_identifier_assigner_id,
        "group_identifier_assigner_display": model.group_identifier_assigner_display,
        "status": fhir_enum(model.status),
        "status_reason_text": model.status_reason_text,
        "status_reason_codings": _plain_coding_list(model.status_reason_codings),
        "priority": fhir_enum(model.priority),
        "do_not_perform": model.do_not_perform,
        "subject_reference": model.subject_reference,
        "subject": computed_subject,
        "subject_type": fhir_enum(model.subject_type),
        "subject_id": model.subject_id,
        "subject_display": model.subject_display,
        "encounter_reference": model.encounter_reference,
        "encounter": computed_encounter,
        "encounter_type": fhir_enum(model.encounter_type),
        "encounter_id": model.encounter_id,
        "encounter_display": model.encounter_display,
        "occurrence_date_time": fhir_instant(model.occurrence_date_time)
        if model.occurrence_date_time
        else None,
        "occurrence_period_start": fhir_instant(model.occurrence_period_start)
        if model.occurrence_period_start
        else None,
        "occurrence_period_end": fhir_instant(model.occurrence_period_end)
        if model.occurrence_period_end
        else None,
        "authored_on": fhir_instant(model.authored_on) if model.authored_on else None,
        "requester_reference": model.requester_reference,
        "requester": computed_requester,
        "requester_type": fhir_enum(model.requester_type),
        "requester_id": model.requester_id,
        "requester_display": model.requester_display,
        "sender_reference": model.sender_reference,
        "sender": computed_sender,
        "sender_type": fhir_enum(model.sender_type),
        "sender_id": model.sender_id,
        "sender_display": model.sender_display,
        "identifier": [_plain_identifier(i) for i in model.identifiers or []]
        if model.identifiers
        else None,
        "based_on": [_plain_reference_row(b) for b in model.based_on_list or []]
        if model.based_on_list
        else None,
        "replaces": [_plain_reference_row(r) for r in model.replaces_list or []]
        if model.replaces_list
        else None,
        "category": [
            {
                "id": c.id,
                "text": c.text,
                "codings": _plain_coding_list(c.codings),
            }
            for c in model.categories or []
        ]
        if model.categories
        else None,
        "medium": [
            {
                "id": m.id,
                "text": m.text,
                "codings": _plain_coding_list(m.codings),
            }
            for m in model.medium_list or []
        ]
        if model.medium_list
        else None,
        "about": [_plain_reference_row(a) for a in model.about_list or []]
        if model.about_list
        else None,
        "payload": [_plain_payload(p) for p in model.payloads or []]
        if model.payloads
        else None,
        "recipient": [_plain_reference_row(rec) for rec in model.recipients or []]
        if model.recipients
        else None,
        "reason_code": [
            {
                "id": rc.id,
                "text": rc.text,
                "codings": _plain_coding_list(rc.codings),
            }
            for rc in model.reason_codes or []
        ]
        if model.reason_codes
        else None,
        "reason_reference": [
            _plain_reference_row(rr) for rr in model.reason_references or []
        ]
        if model.reason_references
        else None,
        "note": [_plain_note(n) for n in model.notes or []]
        if model.notes
        else None,
        "extension": model.extension or None,
        "tenant_id": model.tenant_id,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": fhir_instant(model.created_at) if model.created_at else None,
        "updated_at": fhir_instant(model.updated_at) if model.updated_at else None,
    }

    return {k: v for k, v in result.items() if v is not None}
