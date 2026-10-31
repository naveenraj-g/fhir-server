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


def _fhir_reference_row(row) -> dict | None:
    return _fhir_ref(
        row.reference_reference,
        row.reference_type,
        row.reference_id,
        row.reference_display,
    )


def _fhir_identifier(i: CommunicationRequestIdentifier) -> dict | None:
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
    assigner = _fhir_ref(
        i.assigner_reference,
        i.assigner_type,
        i.assigner_id,
        i.assigner_display,
    )
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_group_identifier(model: CommunicationRequestModel) -> dict | None:
    entry: dict = {}
    if model.group_identifier_use:
        entry["use"] = fhir_enum(model.group_identifier_use)
    if model.group_identifier_system:
        entry["system"] = model.group_identifier_system
    if model.group_identifier_value:
        entry["value"] = model.group_identifier_value
    if model.group_identifier_period_start or model.group_identifier_period_end:
        period: dict = {}
        if model.group_identifier_period_start:
            period["start"] = fhir_instant(model.group_identifier_period_start)
        if model.group_identifier_period_end:
            period["end"] = fhir_instant(model.group_identifier_period_end)
        entry["period"] = period
    assigner = _fhir_ref(
        model.group_identifier_assigner_reference,
        model.group_identifier_assigner_type,
        model.group_identifier_assigner_id,
        model.group_identifier_assigner_display,
    )
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_note(n: CommunicationRequestNote) -> dict | None:
    entry: dict = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    elif n.author_reference or (n.author_type and n.author_id):
        author_ref = _fhir_ref(
            n.author_reference, n.author_type, n.author_id, n.author_display
        )
        if author_ref:
            entry["authorReference"] = author_ref
    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.text:
        entry["text"] = n.text
    return entry or None


def _fhir_attachment_from_row(row: CommunicationRequestPayload) -> dict | None:
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


def _fhir_payload(p: CommunicationRequestPayload) -> dict | None:
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
    elif p.content_reference_reference or (p.content_reference_type and p.content_reference_id):
        ref = _fhir_ref(
            p.content_reference_reference,
            p.content_reference_type,
            p.content_reference_id,
            p.content_reference_display,
        )
        if ref:
            entry["contentReference"] = ref
    return entry or None


def _fhir_meta(model: CommunicationRequestModel) -> dict:
    meta: dict = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    elif model.created_at:
        meta["lastUpdated"] = fhir_instant(model.created_at)
    return meta


def to_fhir_communication_request(model: CommunicationRequestModel) -> dict:
    """Map SQLAlchemy CommunicationRequestModel to a FHIR R4 CommunicationRequest resource dict."""
    result: dict[str, Any] = {
        "resourceType": "CommunicationRequest",
        "id": str(model.communication_request_id),
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

    if model.based_on_list:
        based_on = [
            item
            for item in (_fhir_reference_row(b) for b in model.based_on_list)
            if item is not None
        ]
        if based_on:
            result["basedOn"] = based_on

    if model.replaces_list:
        replaces = [
            item
            for item in (_fhir_reference_row(r) for r in model.replaces_list)
            if item is not None
        ]
        if replaces:
            result["replaces"] = replaces

    group_id = _fhir_group_identifier(model)
    if group_id:
        result["groupIdentifier"] = group_id

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

    if model.do_not_perform is not None:
        result["doNotPerform"] = model.do_not_perform

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

    subject = _fhir_ref(
        model.subject_reference,
        model.subject_type,
        model.subject_id,
        model.subject_display,
    )
    if subject:
        result["subject"] = subject

    if model.about_list:
        about = [
            item
            for item in (_fhir_reference_row(a) for a in model.about_list)
            if item is not None
        ]
        if about:
            result["about"] = about

    encounter = _fhir_ref(
        model.encounter_reference,
        model.encounter_type,
        model.encounter_id,
        model.encounter_display,
    )
    if encounter:
        result["encounter"] = encounter

    if model.payloads:
        payloads = [
            item
            for item in (_fhir_payload(p) for p in model.payloads)
            if item is not None
        ]
        if payloads:
            result["payload"] = payloads

    if model.occurrence_date_time is not None:
        result["occurrenceDateTime"] = fhir_instant(model.occurrence_date_time)
    elif model.occurrence_period_start or model.occurrence_period_end:
        period: dict = {}
        if model.occurrence_period_start:
            period["start"] = fhir_instant(model.occurrence_period_start)
        if model.occurrence_period_end:
            period["end"] = fhir_instant(model.occurrence_period_end)
        result["occurrencePeriod"] = period

    if model.authored_on is not None:
        result["authoredOn"] = fhir_instant(model.authored_on)

    requester = _fhir_ref(
        model.requester_reference,
        model.requester_type,
        model.requester_id,
        model.requester_display,
    )
    if requester:
        result["requester"] = requester

    if model.recipients:
        recipients = [
            item
            for item in (_fhir_reference_row(rec) for rec in model.recipients)
            if item is not None
        ]
        if recipients:
            result["recipient"] = recipients

    sender = _fhir_ref(
        model.sender_reference,
        model.sender_type,
        model.sender_id,
        model.sender_display,
    )
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
