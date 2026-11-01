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


def _plain_identifier(i: CommunicationIdentifier) -> dict:
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


def _plain_note(n: CommunicationNote) -> dict:
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


def _plain_payload(p: CommunicationPayload) -> dict:
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
        **_plain_reference_fields(p, "content_reference"),
        "created_at": fhir_instant(p.created_at) if hasattr(p, "created_at") else None,
        "updated_at": fhir_instant(p.updated_at) if hasattr(p, "updated_at") else None,
        "created_by": getattr(p, "created_by", None),
        "updated_by": getattr(p, "updated_by", None),
        "tenant_id": getattr(p, "tenant_id", None),
    }


def to_plain_communication(model: CommunicationModel) -> dict:
    """Map SQLAlchemy CommunicationModel to a plain snake_case dict."""
    result: dict[str, Any] = {
        "id": model.communication_id,
        "instantiates_canonical": list(model.instantiates_canonical) if model.instantiates_canonical else None,
        "instantiates_uri": list(model.instantiates_uri) if model.instantiates_uri else None,
        "status": fhir_enum(model.status),
        "status_reason_text": model.status_reason_text,
        "status_reason_codings": _plain_coding_list(model.status_reason_codings) if model.status_reason_codings else None,
        "priority": fhir_enum(model.priority),
        **_plain_reference_fields(model, "subject"),
        "topic_text": model.topic_text,
        "topic_codings": _plain_coding_list(model.topic_codings) if model.topic_codings else None,
        **_plain_reference_fields(model, "encounter"),
        "sent": fhir_instant(model.sent) if model.sent else None,
        "received": fhir_instant(model.received) if model.received else None,
        **_plain_reference_fields(model, "sender"),
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
