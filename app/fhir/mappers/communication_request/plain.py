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


def _plain_reference_fields(obj, prefix: str) -> dict:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    computed = raw_reference or (
        f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None
    )
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)
    return {
        f"{prefix}_reference": raw_reference,
        prefix: computed,
        f"{prefix}_type": fhir_enum(ref_type),
        f"{prefix}_id": ref_id,
        f"{prefix}_display": getattr(obj, f"{prefix}_display", None),
        f"{prefix}_identifier_use": fhir_enum(
            getattr(obj, f"{prefix}_identifier_use", None)
        ),
        f"{prefix}_identifier_type_system": getattr(
            obj, f"{prefix}_identifier_type_system", None
        ),
        f"{prefix}_identifier_type_version": getattr(
            obj, f"{prefix}_identifier_type_version", None
        ),
        f"{prefix}_identifier_type_code": getattr(
            obj, f"{prefix}_identifier_type_code", None
        ),
        f"{prefix}_identifier_type_display": getattr(
            obj, f"{prefix}_identifier_type_display", None
        ),
        f"{prefix}_identifier_type_text": getattr(
            obj, f"{prefix}_identifier_type_text", None
        ),
        f"{prefix}_identifier_type_user_selected": getattr(
            obj, f"{prefix}_identifier_type_user_selected", None
        ),
        f"{prefix}_identifier_system": getattr(
            obj, f"{prefix}_identifier_system", None
        ),
        f"{prefix}_identifier_value": getattr(obj, f"{prefix}_identifier_value", None),
        f"{prefix}_identifier_period_start": fhir_instant(id_period_start)
        if id_period_start
        else None,
        f"{prefix}_identifier_period_end": fhir_instant(id_period_end)
        if id_period_end
        else None,
    }


def _plain_reference_row(row) -> dict:
    return {
        "id": row.id,
        **_plain_reference_fields(row, "reference"),
        "created_at": fhir_instant(row.created_at) if hasattr(row, "created_at") else None,
        "updated_at": fhir_instant(row.updated_at) if hasattr(row, "updated_at") else None,
        "created_by": getattr(row, "created_by", None),
        "updated_by": getattr(row, "updated_by", None),
        "tenant_id": getattr(row, "tenant_id", None),
    }


def _plain_identifier(i: CommunicationRequestIdentifier) -> dict:
    return {
        "id": i.id,
        "use": fhir_enum(i.use),
        "type_text": i.type_text,
        "type_codings": _plain_coding_list(getattr(i, "type_codings", None)),
        "system": i.system,
        "value": i.value,
        "period_start": fhir_instant(i.period_start) if i.period_start else None,
        "period_end": fhir_instant(i.period_end) if i.period_end else None,
        **_plain_reference_fields(i, "assigner"),
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
        **_plain_reference_fields(n, "author"),
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
    return {
        "id": p.id,
        "content_string": p.content_string,
        "content_attachment": att,
        **_plain_reference_fields(p, "content_reference"),
        "created_at": fhir_instant(p.created_at) if hasattr(p, "created_at") else None,
        "updated_at": fhir_instant(p.updated_at) if hasattr(p, "updated_at") else None,
        "created_by": getattr(p, "created_by", None),
        "updated_by": getattr(p, "updated_by", None),
        "tenant_id": getattr(p, "tenant_id", None),
    }


def to_plain_communication_request(model: CommunicationRequestModel) -> dict:
    """Map SQLAlchemy CommunicationRequestModel to a plain snake_case dictionary."""
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
        **_plain_reference_fields(model, "group_identifier_assigner"),
        "status": fhir_enum(model.status),
        "status_reason_text": model.status_reason_text,
        "status_reason_codings": _plain_coding_list(model.status_reason_codings),
        "priority": fhir_enum(model.priority),
        "do_not_perform": model.do_not_perform,
        **_plain_reference_fields(model, "subject"),
        **_plain_reference_fields(model, "encounter"),
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
        **_plain_reference_fields(model, "requester"),
        **_plain_reference_fields(model, "sender"),
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
