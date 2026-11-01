"""Payload -> FHIR JSON conversion for Communication.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(CommunicationCreateSchema / CommunicationPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.schemas.communication.input import (
        CommunicationCategoryInput,
        CommunicationCreateSchema,
        CommunicationIdentifierInput,
        CommunicationNoteInput,
        CommunicationPatchSchema,
        CommunicationPayloadInput,
        CommunicationReferenceInput,
    )

_STATUS_REASON_FIELDS = {"status_reason_coding", "status_reason_text"}
_SUBJECT_FIELDS = {"subject", "subject_display"}
_TOPIC_FIELDS = {"topic_coding", "topic_text"}
_ENCOUNTER_FIELDS = {"encounter", "encounter_display"}
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
    # Model object (CommunicationReferenceInput)
    result = {}
    r = getattr(ref, "reference", None)
    if r:
        result["reference"] = r
    d = getattr(ref, "display", None) or display
    if d:
        result["display"] = d
    return result or None


def _identifier_from_payload(i: CommunicationIdentifierInput) -> dict | None:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    if i.type_coding or i.type_text:
        type_cc = _codeable_concept_from_payload(i.type_coding, i.type_text)
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
    if i.assigner or i.assigner_display:
        assigner = _ref_from_payload(i.assigner, i.assigner_display)
        if assigner:
            entry["assigner"] = assigner
    return entry or None


def _note_from_payload(n: CommunicationNoteInput) -> dict | None:
    entry: dict = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    elif n.author_reference or n.author_display:
        author_ref = _ref_from_payload(n.author_reference, n.author_display)
        if author_ref:
            entry["authorReference"] = author_ref
    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.text:
        entry["text"] = n.text
    return entry or None


def _attachment_from_payload(att: Any) -> dict | None:
    if not att:
        return None
    if isinstance(att, dict):
        result: dict = {}
        if att.get("content_type") or att.get("contentType"):
            result["contentType"] = att.get("content_type") or att.get("contentType")
        if att.get("language"):
            result["language"] = att["language"]
        if att.get("data"):
            result["data"] = att["data"]
        if att.get("url"):
            result["url"] = att["url"]
        if att.get("size") is not None:
            result["size"] = int(att["size"])
        if att.get("hash"):
            result["hash"] = att["hash"]
        if att.get("title"):
            result["title"] = att["title"]
        if att.get("creation"):
            result["creation"] = fhir_instant(att["creation"])
        return result or None
    result = {}
    ct = getattr(att, "content_type", None) or getattr(att, "contentType", None)
    if ct:
        result["contentType"] = ct
    if getattr(att, "language", None):
        result["language"] = att.language
    if getattr(att, "data", None):
        result["data"] = att.data
    if getattr(att, "url", None):
        result["url"] = att.url
    if getattr(att, "size", None) is not None:
        result["size"] = int(att.size)
    if getattr(att, "hash", None):
        result["hash"] = att.hash
    if getattr(att, "title", None):
        result["title"] = att.title
    if getattr(att, "creation", None):
        result["creation"] = fhir_instant(att.creation)
    return result or None


def _payload_item_from_payload(p: CommunicationPayloadInput) -> dict | None:
    entry: dict = {}
    if p.content_string is not None:
        entry["contentString"] = p.content_string
    elif p.content_attachment is not None:
        att = _attachment_from_payload(p.content_attachment)
        if att:
            entry["contentAttachment"] = att
    elif p.content_reference or p.content_reference_display:
        ref = _ref_from_payload(p.content_reference, p.content_reference_display)
        if ref:
            entry["contentReference"] = ref
    return entry or None


def payload_to_fhir_communication(payload: CommunicationCreateSchema) -> dict:
    """Map CommunicationCreateSchema to a FHIR R4 Communication dict (pre-insert)."""
    result: dict[str, Any] = {
        "resourceType": "Communication",
    }

    if payload.identifier:
        identifiers = [
            item
            for item in (_identifier_from_payload(i) for i in payload.identifier)
            if item is not None
        ]
        if identifiers:
            result["identifier"] = identifiers

    if payload.instantiates_canonical:
        result["instantiatesCanonical"] = list(payload.instantiates_canonical)

    if payload.instantiates_uri:
        result["instantiatesUri"] = list(payload.instantiates_uri)

    if payload.based_on:
        based_on = [
            item
            for item in (_ref_from_payload(b) for b in payload.based_on)
            if item is not None
        ]
        if based_on:
            result["basedOn"] = based_on

    if payload.part_of:
        part_of = [
            item
            for item in (_ref_from_payload(p) for p in payload.part_of)
            if item is not None
        ]
        if part_of:
            result["partOf"] = part_of

    if payload.in_response_to:
        in_response_to = [
            item
            for item in (_ref_from_payload(r) for r in payload.in_response_to)
            if item is not None
        ]
        if in_response_to:
            result["inResponseTo"] = in_response_to

    if payload.status:
        result["status"] = fhir_enum(payload.status)

    if payload.status_reason_coding or payload.status_reason_text:
        status_reason = _codeable_concept_from_payload(
            payload.status_reason_coding, payload.status_reason_text
        )
        if status_reason:
            result["statusReason"] = status_reason

    if payload.category:
        categories = [
            item
            for item in (
                _codeable_concept_from_payload(c.coding, c.text)
                for c in payload.category
            )
            if item is not None
        ]
        if categories:
            result["category"] = categories

    if payload.priority:
        result["priority"] = fhir_enum(payload.priority)

    if payload.medium:
        medium = [
            item
            for item in (
                _codeable_concept_from_payload(m.coding, m.text)
                for m in payload.medium
            )
            if item is not None
        ]
        if medium:
            result["medium"] = medium

    if payload.subject or payload.subject_display:
        subject = _ref_from_payload(payload.subject, payload.subject_display)
        if subject:
            result["subject"] = subject

    if payload.topic_coding or payload.topic_text:
        topic = _codeable_concept_from_payload(
            payload.topic_coding, payload.topic_text
        )
        if topic:
            result["topic"] = topic

    if payload.about:
        about = [
            item
            for item in (_ref_from_payload(a) for a in payload.about)
            if item is not None
        ]
        if about:
            result["about"] = about

    if payload.encounter or payload.encounter_display:
        encounter = _ref_from_payload(payload.encounter, payload.encounter_display)
        if encounter:
            result["encounter"] = encounter

    if payload.sent is not None:
        result["sent"] = fhir_instant(payload.sent)

    if payload.received is not None:
        result["received"] = fhir_instant(payload.received)

    if payload.recipient:
        recipients = [
            item
            for item in (_ref_from_payload(rec) for rec in payload.recipient)
            if item is not None
        ]
        if recipients:
            result["recipient"] = recipients

    if payload.sender or payload.sender_display:
        sender = _ref_from_payload(payload.sender, payload.sender_display)
        if sender:
            result["sender"] = sender

    if payload.reason_code:
        reason_codes = [
            item
            for item in (
                _codeable_concept_from_payload(rc.coding, rc.text)
                for rc in payload.reason_code
            )
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

    if payload.payload:
        payloads = [
            item
            for item in (_payload_item_from_payload(p) for p in payload.payload)
            if item is not None
        ]
        if payloads:
            result["payload"] = payloads

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


def patch_fragment_to_fhir_communication(
    patch: CommunicationPatchSchema,
) -> tuple[dict, set[str]]:
    """Map touched fields of CommunicationPatchSchema to FHIR JSON fragment and touched keys."""
    touched_schema_fields = patch.model_fields_set
    fragment: dict[str, Any] = {}
    touched_fhir_keys: set[str] = set()

    if "identifier" in touched_schema_fields:
        touched_fhir_keys.add("identifier")
        if patch.identifier is not None:
            fragment["identifier"] = [
                item
                for item in (_identifier_from_payload(i) for i in patch.identifier)
                if item is not None
            ]
        else:
            fragment["identifier"] = None

    if "instantiates_canonical" in touched_schema_fields:
        touched_fhir_keys.add("instantiatesCanonical")
        fragment["instantiatesCanonical"] = (
            list(patch.instantiates_canonical) if patch.instantiates_canonical is not None else None
        )

    if "instantiates_uri" in touched_schema_fields:
        touched_fhir_keys.add("instantiatesUri")
        fragment["instantiatesUri"] = (
            list(patch.instantiates_uri) if patch.instantiates_uri is not None else None
        )

    if "based_on" in touched_schema_fields:
        touched_fhir_keys.add("basedOn")
        if patch.based_on is not None:
            fragment["basedOn"] = [
                item
                for item in (_ref_from_payload(b) for b in patch.based_on)
                if item is not None
            ]
        else:
            fragment["basedOn"] = None

    if "part_of" in touched_schema_fields:
        touched_fhir_keys.add("partOf")
        if patch.part_of is not None:
            fragment["partOf"] = [
                item
                for item in (_ref_from_payload(p) for p in patch.part_of)
                if item is not None
            ]
        else:
            fragment["partOf"] = None

    if "in_response_to" in touched_schema_fields:
        touched_fhir_keys.add("inResponseTo")
        if patch.in_response_to is not None:
            fragment["inResponseTo"] = [
                item
                for item in (_ref_from_payload(r) for r in patch.in_response_to)
                if item is not None
            ]
        else:
            fragment["inResponseTo"] = None

    if "status" in touched_schema_fields:
        touched_fhir_keys.add("status")
        fragment["status"] = fhir_enum(patch.status) if patch.status is not None else None

    if touched_schema_fields & _STATUS_REASON_FIELDS:
        touched_fhir_keys.add("statusReason")
        if patch.status_reason_coding or patch.status_reason_text:
            fragment["statusReason"] = _codeable_concept_from_payload(
                patch.status_reason_coding, patch.status_reason_text
            )
        else:
            fragment["statusReason"] = None

    if "category" in touched_schema_fields:
        touched_fhir_keys.add("category")
        if patch.category is not None:
            fragment["category"] = [
                item
                for item in (
                    _codeable_concept_from_payload(c.coding, c.text)
                    for c in patch.category
                )
                if item is not None
            ]
        else:
            fragment["category"] = None

    if "priority" in touched_schema_fields:
        touched_fhir_keys.add("priority")
        fragment["priority"] = fhir_enum(patch.priority) if patch.priority is not None else None

    if "medium" in touched_schema_fields:
        touched_fhir_keys.add("medium")
        if patch.medium is not None:
            fragment["medium"] = [
                item
                for item in (
                    _codeable_concept_from_payload(m.coding, m.text)
                    for m in patch.medium
                )
                if item is not None
            ]
        else:
            fragment["medium"] = None

    if touched_schema_fields & _SUBJECT_FIELDS:
        touched_fhir_keys.add("subject")
        if patch.subject or patch.subject_display:
            fragment["subject"] = _ref_from_payload(patch.subject, patch.subject_display)
        else:
            fragment["subject"] = None

    if touched_schema_fields & _TOPIC_FIELDS:
        touched_fhir_keys.add("topic")
        if patch.topic_coding or patch.topic_text:
            fragment["topic"] = _codeable_concept_from_payload(
                patch.topic_coding, patch.topic_text
            )
        else:
            fragment["topic"] = None

    if "about" in touched_schema_fields:
        touched_fhir_keys.add("about")
        if patch.about is not None:
            fragment["about"] = [
                item
                for item in (_ref_from_payload(a) for a in patch.about)
                if item is not None
            ]
        else:
            fragment["about"] = None

    if touched_schema_fields & _ENCOUNTER_FIELDS:
        touched_fhir_keys.add("encounter")
        if patch.encounter or patch.encounter_display:
            fragment["encounter"] = _ref_from_payload(patch.encounter, patch.encounter_display)
        else:
            fragment["encounter"] = None

    if "sent" in touched_schema_fields:
        touched_fhir_keys.add("sent")
        fragment["sent"] = fhir_instant(patch.sent) if patch.sent is not None else None

    if "received" in touched_schema_fields:
        touched_fhir_keys.add("received")
        fragment["received"] = fhir_instant(patch.received) if patch.received is not None else None

    if "recipient" in touched_schema_fields:
        touched_fhir_keys.add("recipient")
        if patch.recipient is not None:
            fragment["recipient"] = [
                item
                for item in (_ref_from_payload(rec) for rec in patch.recipient)
                if item is not None
            ]
        else:
            fragment["recipient"] = None

    if touched_schema_fields & _SENDER_FIELDS:
        touched_fhir_keys.add("sender")
        if patch.sender or patch.sender_display:
            fragment["sender"] = _ref_from_payload(patch.sender, patch.sender_display)
        else:
            fragment["sender"] = None

    if "reason_code" in touched_schema_fields:
        touched_fhir_keys.add("reasonCode")
        if patch.reason_code is not None:
            fragment["reasonCode"] = [
                item
                for item in (
                    _codeable_concept_from_payload(rc.coding, rc.text)
                    for rc in patch.reason_code
                )
                if item is not None
            ]
        else:
            fragment["reasonCode"] = None

    if "reason_reference" in touched_schema_fields:
        touched_fhir_keys.add("reasonReference")
        if patch.reason_reference is not None:
            fragment["reasonReference"] = [
                item
                for item in (_ref_from_payload(rr) for rr in patch.reason_reference)
                if item is not None
            ]
        else:
            fragment["reasonReference"] = None

    if "payload" in touched_schema_fields:
        touched_fhir_keys.add("payload")
        if patch.payload is not None:
            fragment["payload"] = [
                item
                for item in (_payload_item_from_payload(p) for p in patch.payload)
                if item is not None
            ]
        else:
            fragment["payload"] = None

    if "note" in touched_schema_fields:
        touched_fhir_keys.add("note")
        if patch.note is not None:
            fragment["note"] = [
                item
                for item in (_note_from_payload(n) for n in patch.note)
                if item is not None
            ]
        else:
            fragment["note"] = None

    if "extension" in touched_schema_fields:
        touched_fhir_keys.add("extension")
        fragment["extension"] = patch.extension

    return fragment, touched_fhir_keys
