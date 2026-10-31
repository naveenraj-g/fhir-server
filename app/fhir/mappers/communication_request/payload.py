"""Payload -> FHIR JSON conversion for CommunicationRequest.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(CommunicationRequestCreateSchema / CommunicationRequestPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.schemas.communication_request.input import (
        CommunicationRequestCategoryInput,
        CommunicationRequestCreateSchema,
        CommunicationRequestIdentifierInput,
        CommunicationRequestNoteInput,
        CommunicationRequestPatchSchema,
        CommunicationRequestPayloadInput,
        CommunicationRequestReferenceInput,
    )

_GROUP_IDENTIFIER_FIELDS = {
    "group_identifier_use",
    "group_identifier_system",
    "group_identifier_value",
    "group_identifier_period_start",
    "group_identifier_period_end",
    "group_identifier_assigner",
    "group_identifier_assigner_display",
}
_STATUS_REASON_FIELDS = {"status_reason_coding", "status_reason_text"}
_SUBJECT_FIELDS = {"subject", "subject_display"}
_ENCOUNTER_FIELDS = {"encounter", "encounter_display"}
_OCCURRENCE_FIELDS = {
    "occurrence_date_time",
    "occurrence_period_start",
    "occurrence_period_end",
}
_REQUESTER_FIELDS = {"requester", "requester_display"}
_SENDER_FIELDS = {"sender", "sender_display"}


def _coding_from_payload(c: Any) -> dict:
    if isinstance(c, dict):
        return {
            k: v
            for k, v in {
                "system": c.get("system"),
                "version": c.get("version"),
                "code": c.get("code"),
                "display": c.get("display"),
                "userSelected": c.get("user_selected") or c.get("userSelected"),
            }.items()
            if v is not None
        }
    return {
        k: v
        for k, v in {
            "system": getattr(c, "system", None),
            "version": getattr(c, "version", None),
            "code": getattr(c, "code", None),
            "display": getattr(c, "display", None),
            "userSelected": getattr(c, "user_selected", None),
        }.items()
        if v is not None
    }


def _codeable_concept_from_payload(
    codings: list | None, text: str | None
) -> dict | None:
    coding_list = [_coding_from_payload(c) for c in (codings or [])]
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _ref_from_payload(ref: Any, display: str | None = None) -> dict | None:
    if not ref and not display:
        return None
    if isinstance(ref, dict):
        result = {}
        if ref.get("reference"):
            result["reference"] = ref["reference"]
        disp = ref.get("display") or display
        if disp:
            result["display"] = disp
        return result or None
    if isinstance(ref, str):
        result = {"reference": ref}
        if display:
            result["display"] = display
        return result
    result = {}
    ref_val = getattr(ref, "reference", None)
    if ref_val:
        result["reference"] = ref_val
    disp = getattr(ref, "display", None) or display
    if disp:
        result["display"] = disp
    return result or None


def _identifier_from_payload(i: Any) -> dict | None:
    if not i:
        return None
    entry: dict = {}
    use = getattr(i, "use", None) or (i.get("use") if isinstance(i, dict) else None)
    if use:
        entry["use"] = fhir_enum(use)
    type_codings = getattr(i, "type_coding", None) or (
        i.get("type_coding") if isinstance(i, dict) else None
    )
    type_text = getattr(i, "type_text", None) or (
        i.get("type_text") if isinstance(i, dict) else None
    )
    type_cc = _codeable_concept_from_payload(type_codings, type_text)
    if type_cc:
        entry["type"] = type_cc
    sys = getattr(i, "system", None) or (
        i.get("system") if isinstance(i, dict) else None
    )
    if sys:
        entry["system"] = sys
    val = getattr(i, "value", None) or (i.get("value") if isinstance(i, dict) else None)
    if val:
        entry["value"] = val
    p_start = getattr(i, "period_start", None) or (
        i.get("period_start") if isinstance(i, dict) else None
    )
    p_end = getattr(i, "period_end", None) or (
        i.get("period_end") if isinstance(i, dict) else None
    )
    if p_start or p_end:
        period: dict = {}
        if p_start:
            period["start"] = fhir_instant(p_start)
        if p_end:
            period["end"] = fhir_instant(p_end)
        entry["period"] = period
    assigner_ref = getattr(i, "assigner", None) or (
        i.get("assigner") if isinstance(i, dict) else None
    )
    assigner_disp = getattr(i, "assigner_display", None) or (
        i.get("assigner_display") if isinstance(i, dict) else None
    )
    assigner = _ref_from_payload(assigner_ref, assigner_disp)
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _group_identifier_from_payload(payload: Any) -> dict | None:
    entry: dict = {}
    use = getattr(payload, "group_identifier_use", None) or (
        payload.get("group_identifier_use") if isinstance(payload, dict) else None
    )
    if use:
        entry["use"] = fhir_enum(use)
    sys = getattr(payload, "group_identifier_system", None) or (
        payload.get("group_identifier_system") if isinstance(payload, dict) else None
    )
    if sys:
        entry["system"] = sys
    val = getattr(payload, "group_identifier_value", None) or (
        payload.get("group_identifier_value") if isinstance(payload, dict) else None
    )
    if val:
        entry["value"] = val
    p_start = getattr(payload, "group_identifier_period_start", None) or (
        payload.get("group_identifier_period_start")
        if isinstance(payload, dict)
        else None
    )
    p_end = getattr(payload, "group_identifier_period_end", None) or (
        payload.get("group_identifier_period_end")
        if isinstance(payload, dict)
        else None
    )
    if p_start or p_end:
        period: dict = {}
        if p_start:
            period["start"] = fhir_instant(p_start)
        if p_end:
            period["end"] = fhir_instant(p_end)
        entry["period"] = period
    assigner_ref = getattr(payload, "group_identifier_assigner", None) or (
        payload.get("group_identifier_assigner") if isinstance(payload, dict) else None
    )
    assigner_disp = getattr(payload, "group_identifier_assigner_display", None) or (
        payload.get("group_identifier_assigner_display")
        if isinstance(payload, dict)
        else None
    )
    assigner = _ref_from_payload(assigner_ref, assigner_disp)
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _note_from_payload(n: Any) -> dict | None:
    if not n:
        return None
    entry: dict = {}
    auth_str = getattr(n, "author_string", None) or (
        n.get("author_string") if isinstance(n, dict) else None
    )
    auth_ref = getattr(n, "author_reference", None) or (
        n.get("author_reference") if isinstance(n, dict) else None
    )
    auth_disp = getattr(n, "author_display", None) or (
        n.get("author_display") if isinstance(n, dict) else None
    )
    if auth_str:
        entry["authorString"] = auth_str
    elif auth_ref:
        ref = _ref_from_payload(auth_ref, auth_disp)
        if ref:
            entry["authorReference"] = ref
    time = getattr(n, "time", None) or (n.get("time") if isinstance(n, dict) else None)
    if time:
        entry["time"] = fhir_instant(time)
    text = getattr(n, "text", None) or (n.get("text") if isinstance(n, dict) else None)
    if text:
        entry["text"] = text
    return entry or None


def _attachment_from_payload(att: Any) -> dict | None:
    if not att:
        return None
    if isinstance(att, dict):
        result = {
            "contentType": att.get("content_type") or att.get("contentType"),
            "language": att.get("language"),
            "data": att.get("data"),
            "url": att.get("url"),
            "size": att.get("size"),
            "hash": att.get("hash"),
            "title": att.get("title"),
            "creation": fhir_instant(att.get("creation"))
            if att.get("creation")
            else None,
        }
        return {k: v for k, v in result.items() if v is not None} or None
    result = {
        "contentType": getattr(att, "content_type", None),
        "language": getattr(att, "language", None),
        "data": getattr(att, "data", None),
        "url": getattr(att, "url", None),
        "size": getattr(att, "size", None),
        "hash": getattr(att, "hash", None),
        "title": getattr(att, "title", None),
        "creation": fhir_instant(getattr(att, "creation", None))
        if getattr(att, "creation", None)
        else None,
    }
    return {k: v for k, v in result.items() if v is not None} or None


def _payload_item_from_payload(p: Any) -> dict | None:
    if not p:
        return None
    if isinstance(p, dict):
        entry: dict = {}
        if p.get("content_string") is not None:
            entry["contentString"] = p.get("content_string")
        elif p.get("content_attachment") is not None:
            att = _attachment_from_payload(p.get("content_attachment"))
            if att:
                entry["contentAttachment"] = att
        elif p.get("content_reference") is not None:
            ref = _ref_from_payload(
                p.get("content_reference"), p.get("content_reference_display")
            )
            if ref:
                entry["contentReference"] = ref
        return entry or None

    entry: dict = {}
    content_str = getattr(p, "content_string", None)
    if content_str is not None:
        entry["contentString"] = content_str
    elif getattr(p, "content_attachment", None) is not None:
        att = _attachment_from_payload(getattr(p, "content_attachment"))
        if att:
            entry["contentAttachment"] = att
    elif getattr(p, "content_reference", None) is not None:
        ref = _ref_from_payload(
            getattr(p, "content_reference"),
            getattr(p, "content_reference_display", None),
        )
        if ref:
            entry["contentReference"] = ref
    return entry or None


def _category_from_payload(c: Any) -> dict | None:
    if not c:
        return None
    codings = getattr(c, "coding", None) or (
        c.get("coding") if isinstance(c, dict) else None
    )
    text = getattr(c, "text", None) or (c.get("text") if isinstance(c, dict) else None)
    return _codeable_concept_from_payload(codings, text)


def payload_to_fhir_communication_request(
    payload: CommunicationRequestCreateSchema,
) -> dict:
    """Map CommunicationRequestCreateSchema to FHIR JSON for pre-write validation."""
    result: dict[str, Any] = {
        "resourceType": "CommunicationRequest",
        "id": "validate-only",
        "status": fhir_enum(payload.status),
    }

    if payload.identifier:
        identifiers = [
            item
            for item in (_identifier_from_payload(i) for i in payload.identifier)
            if item is not None
        ]
        if identifiers:
            result["identifier"] = identifiers

    if payload.based_on:
        based_on = [
            item
            for item in (_ref_from_payload(b) for b in payload.based_on)
            if item is not None
        ]
        if based_on:
            result["basedOn"] = based_on

    if payload.replaces:
        replaces = [
            item
            for item in (_ref_from_payload(r) for r in payload.replaces)
            if item is not None
        ]
        if replaces:
            result["replaces"] = replaces

    group_id = _group_identifier_from_payload(payload)
    if group_id:
        result["groupIdentifier"] = group_id

    status_reason = _codeable_concept_from_payload(
        payload.status_reason_coding, payload.status_reason_text
    )
    if status_reason:
        result["statusReason"] = status_reason

    if payload.category:
        categories = [
            item
            for item in (_category_from_payload(c) for c in payload.category)
            if item is not None
        ]
        if categories:
            result["category"] = categories

    if payload.priority:
        result["priority"] = fhir_enum(payload.priority)

    if payload.do_not_perform is not None:
        result["doNotPerform"] = payload.do_not_perform

    if payload.medium:
        medium = [
            item
            for item in (_category_from_payload(m) for m in payload.medium)
            if item is not None
        ]
        if medium:
            result["medium"] = medium

    subject = _ref_from_payload(payload.subject, payload.subject_display)
    if subject:
        result["subject"] = subject

    if payload.about:
        about = [
            item
            for item in (_ref_from_payload(a) for a in payload.about)
            if item is not None
        ]
        if about:
            result["about"] = about

    encounter = _ref_from_payload(payload.encounter, payload.encounter_display)
    if encounter:
        result["encounter"] = encounter

    if payload.payload:
        payloads = [
            item
            for item in (_payload_item_from_payload(p) for p in payload.payload)
            if item is not None
        ]
        if payloads:
            result["payload"] = payloads

    if payload.occurrence_date_time is not None:
        result["occurrenceDateTime"] = fhir_instant(payload.occurrence_date_time)
    elif payload.occurrence_period_start or payload.occurrence_period_end:
        period: dict = {}
        if payload.occurrence_period_start:
            period["start"] = fhir_instant(payload.occurrence_period_start)
        if payload.occurrence_period_end:
            period["end"] = fhir_instant(payload.occurrence_period_end)
        result["occurrencePeriod"] = period

    if payload.authored_on is not None:
        result["authoredOn"] = fhir_instant(payload.authored_on)

    requester = _ref_from_payload(payload.requester, payload.requester_display)
    if requester:
        result["requester"] = requester

    if payload.recipient:
        recipients = [
            item
            for item in (_ref_from_payload(rec) for rec in payload.recipient)
            if item is not None
        ]
        if recipients:
            result["recipient"] = recipients

    sender = _ref_from_payload(payload.sender, payload.sender_display)
    if sender:
        result["sender"] = sender

    if payload.reason_code:
        reason_codes = [
            item
            for item in (_category_from_payload(rc) for rc in payload.reason_code)
            if item is not None
        ]
        if reason_codes:
            result["reasonCode"] = reason_codes

    if payload.reason_reference:
        reason_refs = [
            item
            for item in (_ref_from_payload(rr) for rr in payload.reason_reference)
            if item is not None
        ]
        if reason_refs:
            result["reasonReference"] = reason_refs

    if payload.note:
        notes = [
            item
            for item in (_note_from_payload(n) for n in payload.note)
            if item is not None
        ]
        if notes:
            result["note"] = notes

    if payload.extension:
        result["extension"] = payload.extension

    return {k: v for k, v in result.items() if v is not None}


def patch_fragment_to_fhir_communication_request(
    payload: CommunicationRequestPatchSchema,
) -> tuple[dict, set[str]]:
    """Convert a partial patch payload to a FHIR fragment dictionary and touched fields set."""
    fields_set = payload.model_fields_set
    fragment: dict[str, Any] = {}
    touched: set[str] = set()

    if "status" in fields_set:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = fhir_enum(payload.status)

    if "priority" in fields_set:
        touched.add("priority")
        if payload.priority is not None:
            fragment["priority"] = fhir_enum(payload.priority)

    if "do_not_perform" in fields_set:
        touched.add("doNotPerform")
        if payload.do_not_perform is not None:
            fragment["doNotPerform"] = payload.do_not_perform

    if _GROUP_IDENTIFIER_FIELDS & fields_set:
        touched.add("groupIdentifier")
        group_id = _group_identifier_from_payload(payload)
        if group_id:
            fragment["groupIdentifier"] = group_id

    if _STATUS_REASON_FIELDS & fields_set:
        touched.add("statusReason")
        status_reason = _codeable_concept_from_payload(
            payload.status_reason_coding, payload.status_reason_text
        )
        if status_reason:
            fragment["statusReason"] = status_reason

    if "category" in fields_set:
        touched.add("category")
        if payload.category is not None:
            fragment["category"] = [
                item
                for item in (_category_from_payload(c) for c in payload.category)
                if item is not None
            ]

    if "medium" in fields_set:
        touched.add("medium")
        if payload.medium is not None:
            fragment["medium"] = [
                item
                for item in (_category_from_payload(m) for m in payload.medium)
                if item is not None
            ]

    if _SUBJECT_FIELDS & fields_set:
        touched.add("subject")
        subject = _ref_from_payload(payload.subject, payload.subject_display)
        if subject:
            fragment["subject"] = subject

    if "about" in fields_set:
        touched.add("about")
        if payload.about is not None:
            fragment["about"] = [
                item
                for item in (_ref_from_payload(a) for a in payload.about)
                if item is not None
            ]

    if _ENCOUNTER_FIELDS & fields_set:
        touched.add("encounter")
        encounter = _ref_from_payload(payload.encounter, payload.encounter_display)
        if encounter:
            fragment["encounter"] = encounter

    if "payload" in fields_set:
        touched.add("payload")
        if payload.payload is not None:
            fragment["payload"] = [
                item
                for item in (_payload_item_from_payload(p) for p in payload.payload)
                if item is not None
            ]

    if _OCCURRENCE_FIELDS & fields_set:
        touched.add("occurrenceDateTime")
        touched.add("occurrencePeriod")
        if payload.occurrence_date_time is not None:
            fragment["occurrenceDateTime"] = fhir_instant(payload.occurrence_date_time)
        elif payload.occurrence_period_start or payload.occurrence_period_end:
            period: dict = {}
            if payload.occurrence_period_start:
                period["start"] = fhir_instant(payload.occurrence_period_start)
            if payload.occurrence_period_end:
                period["end"] = fhir_instant(payload.occurrence_period_end)
            fragment["occurrencePeriod"] = period

    if "authored_on" in fields_set:
        touched.add("authoredOn")
        if payload.authored_on is not None:
            fragment["authoredOn"] = fhir_instant(payload.authored_on)

    if _REQUESTER_FIELDS & fields_set:
        touched.add("requester")
        requester = _ref_from_payload(payload.requester, payload.requester_display)
        if requester:
            fragment["requester"] = requester

    if "recipient" in fields_set:
        touched.add("recipient")
        if payload.recipient is not None:
            fragment["recipient"] = [
                item
                for item in (_ref_from_payload(rec) for rec in payload.recipient)
                if item is not None
            ]

    if _SENDER_FIELDS & fields_set:
        touched.add("sender")
        sender = _ref_from_payload(payload.sender, payload.sender_display)
        if sender:
            fragment["sender"] = sender

    if "reason_code" in fields_set:
        touched.add("reasonCode")
        if payload.reason_code is not None:
            fragment["reasonCode"] = [
                item
                for item in (_category_from_payload(rc) for rc in payload.reason_code)
                if item is not None
            ]

    if "reason_reference" in fields_set:
        touched.add("reasonReference")
        if payload.reason_reference is not None:
            fragment["reasonReference"] = [
                item
                for item in (_ref_from_payload(rr) for rr in payload.reason_reference)
                if item is not None
            ]

    if "note" in fields_set:
        touched.add("note")
        if payload.note is not None:
            fragment["note"] = [
                item
                for item in (_note_from_payload(n) for n in payload.note)
                if item is not None
            ]

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                item
                for item in (_identifier_from_payload(i) for i in payload.identifier)
                if item is not None
            ]

    if "based_on" in fields_set:
        touched.add("basedOn")
        if payload.based_on is not None:
            fragment["basedOn"] = [
                item
                for item in (_ref_from_payload(b) for b in payload.based_on)
                if item is not None
            ]

    if "replaces" in fields_set:
        touched.add("replaces")
        if payload.replaces is not None:
            fragment["replaces"] = [
                item
                for item in (_ref_from_payload(r) for r in payload.replaces)
                if item is not None
            ]

    if "extension" in fields_set:
        touched.add("extension")
        if payload.extension is not None:
            fragment["extension"] = payload.extension

    return fragment, touched
