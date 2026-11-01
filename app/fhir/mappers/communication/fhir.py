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


def _fhir_coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            k: v
            for k, v in {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "userSelected": c.user_selected,
            }.items()
            if v is not None
        }
        if entry:
            result.append(entry)
    return result


def _fhir_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_ref(
    ref_raw: str | None,
    ref_type: Any,
    ref_id: int | None,
    display: str | None,
) -> dict | None:
    result: dict = {}
    if ref_raw:
        result["reference"] = ref_raw
    elif ref_type and ref_id:
        result["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        result["display"] = display
    return result or None


def _fhir_reference(obj, prefix: str) -> dict | None:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    elif ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_type_user_selected = getattr(obj, f"{prefix}_identifier_type_user_selected", None)
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
                type_cc["coding"] = [
                    {
                        k: v
                        for k, v in {
                            "system": id_type_system,
                            "version": id_type_version,
                            "code": id_type_code,
                            "display": id_type_display,
                            "userSelected": id_type_user_selected,
                        }.items()
                        if v is not None
                    }
                ]
            if id_type_text:
                type_cc["text"] = id_type_text
            identifier["type"] = type_cc
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_period_start or id_period_end:
            identifier["period"] = {
                k: v
                for k, v in {"start": fhir_instant(id_period_start), "end": fhir_instant(id_period_end)}.items()
                if v
            }
        entry["identifier"] = identifier
    return entry or None


def _fhir_reference_row(row) -> dict | None:
    return _fhir_reference(row, "reference")


def _fhir_identifier(i: CommunicationIdentifier) -> dict | None:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = _fhir_codeable_concept(getattr(i, "type_codings", None), i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        period: dict = {}
        if i.period_start:
            period["start"] = fhir_instant(i.period_start)
        if i.period_end:
            period["end"] = fhir_instant(i.period_end)
        entry["period"] = period
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_note(n: CommunicationNote) -> dict | None:
    entry: dict = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    else:
        author_ref = _fhir_reference(n, "author")
        if author_ref:
            entry["authorReference"] = author_ref
    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.text:
        entry["text"] = n.text
    return entry or None


def _fhir_attachment_from_row(row: CommunicationPayload) -> dict | None:
    att: dict = {}
    if row.content_type:
        att["contentType"] = row.content_type
    if row.language:
        att["language"] = row.language
    if row.data:
        att["data"] = row.data
    if row.url:
        att["url"] = row.url
    if row.size is not None:
        att["size"] = int(row.size)
    if row.hash:
        att["hash"] = row.hash
    if row.title:
        att["title"] = row.title
    if row.creation:
        att["creation"] = fhir_instant(row.creation)
    return att or None


def _fhir_payload(p: CommunicationPayload) -> dict | None:
    entry: dict = {}
    if p.content_string is not None:
        entry["contentString"] = p.content_string
    elif (
        p.data
        or p.url
        or p.title
        or p.content_type
    ):
        att = _fhir_attachment_from_row(p)
        if att:
            entry["contentAttachment"] = att
    else:
        ref = _fhir_reference(p, "content_reference")
        if ref:
            entry["contentReference"] = ref
    return entry or None


def _fhir_meta(model: CommunicationModel) -> dict:
    meta: dict = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    elif model.created_at:
        meta["lastUpdated"] = fhir_instant(model.created_at)
    return meta


def to_fhir_communication(model: CommunicationModel) -> dict:
    """Map SQLAlchemy CommunicationModel to a FHIR R4 Communication resource dict."""
    result: dict[str, Any] = {
        "resourceType": "Communication",
        "id": str(model.communication_id),
    }

    meta = _fhir_meta(model)
    if meta:
        result["meta"] = meta

    if model.identifiers:
        identifiers = [
            item
            for item in (_fhir_identifier(i) for i in model.identifiers)
            if item is not None
        ]
        if identifiers:
            result["identifier"] = identifiers

    if model.instantiates_canonical:
        result["instantiatesCanonical"] = list(model.instantiates_canonical)

    if model.instantiates_uri:
        result["instantiatesUri"] = list(model.instantiates_uri)

    if model.based_on_list:
        based_on = [
            item
            for item in (_fhir_reference_row(b) for b in model.based_on_list)
            if item is not None
        ]
        if based_on:
            result["basedOn"] = based_on

    if model.part_of_list:
        part_of = [
            item
            for item in (_fhir_reference_row(p) for p in model.part_of_list)
            if item is not None
        ]
        if part_of:
            result["partOf"] = part_of

    if model.in_response_to_list:
        in_response_to = [
            item
            for item in (_fhir_reference_row(r) for r in model.in_response_to_list)
            if item is not None
        ]
        if in_response_to:
            result["inResponseTo"] = in_response_to

    result["status"] = fhir_enum(model.status)

    status_reason = _fhir_codeable_concept(
        model.status_reason_codings, model.status_reason_text
    )
    if status_reason:
        result["statusReason"] = status_reason

    if model.categories:
        categories = [
            item
            for item in (
                _fhir_codeable_concept(c.codings, c.text)
                for c in model.categories
            )
            if item is not None
        ]
        if categories:
            result["category"] = categories

    if model.priority:
        result["priority"] = fhir_enum(model.priority)

    if model.medium_list:
        medium = [
            item
            for item in (
                _fhir_codeable_concept(m.codings, m.text)
                for m in model.medium_list
            )
            if item is not None
        ]
        if medium:
            result["medium"] = medium

    subject = _fhir_reference(model, "subject")
    if subject:
        result["subject"] = subject

    topic = _fhir_codeable_concept(
        model.topic_codings, model.topic_text
    )
    if topic:
        result["topic"] = topic

    if model.about_list:
        about = [
            item
            for item in (_fhir_reference_row(a) for a in model.about_list)
            if item is not None
        ]
        if about:
            result["about"] = about

    encounter = _fhir_reference(model, "encounter")
    if encounter:
        result["encounter"] = encounter

    if model.sent is not None:
        result["sent"] = fhir_instant(model.sent)

    if model.received is not None:
        result["received"] = fhir_instant(model.received)

    if model.recipients:
        recipients = [
            item
            for item in (_fhir_reference_row(rec) for rec in model.recipients)
            if item is not None
        ]
        if recipients:
            result["recipient"] = recipients

    sender = _fhir_reference(model, "sender")
    if sender:
        result["sender"] = sender

    if model.reason_codes:
        reason_codes = [
            item
            for item in (
                _fhir_codeable_concept(rc.codings, rc.text)
                for rc in model.reason_codes
            )
            if item is not None
        ]
        if reason_codes:
            result["reasonCode"] = reason_codes

    if model.reason_references:
        reason_refs = [
            item
            for item in (
                _fhir_reference_row(rr) for rr in model.reason_references
            )
            if item is not None
        ]
        if reason_refs:
            result["reasonReference"] = reason_refs

    if model.payloads:
        payloads = [
            item
            for item in (_fhir_payload(p) for p in model.payloads)
            if item is not None
        ]
        if payloads:
            result["payload"] = payloads

    if model.notes:
        notes = [
            item
            for item in (_fhir_note(n) for n in model.notes)
            if item is not None
        ]
        if notes:
            result["note"] = notes

    if model.extension:
        result["extension"] = model.extension

    return {k: v for k, v in result.items() if v is not None}
