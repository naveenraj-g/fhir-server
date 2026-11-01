"""Payload -> FHIR JSON conversion for DocumentReference.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(DocumentReferenceCreateSchema / DocumentReferencePatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.document_reference.input import (
        DocumentReferenceCodeableConceptInput,
        DocumentReferenceContentInput,
        DocumentReferenceContextInput,
        DocumentReferenceCreateSchema,
        DocumentReferenceIdentifierInput,
        DocumentReferencePatchSchema,
        DocumentReferenceRelatesToInput,
    )


def _reference_from_payload(obj: Any, prefix: str) -> dict | None:
    if obj is None:
        return None

    def _get(field):
        return obj.get(field) if isinstance(obj, dict) else getattr(obj, field, None)

    raw_reference = _get(prefix)
    if raw_reference is None and prefix != "reference":
        raw_reference = _get(f"{prefix}_reference")
    display = _get(f"{prefix}_display")
    if display is None and prefix == "reference":
        display = _get("display")

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    if display:
        entry["display"] = display

    id_use = _get(f"{prefix}_identifier_use") or _get("identifier_use")
    id_type_system = _get(f"{prefix}_identifier_type_system") or _get("identifier_type_system")
    id_type_version = _get(f"{prefix}_identifier_type_version") or _get("identifier_type_version")
    id_type_code = _get(f"{prefix}_identifier_type_code") or _get("identifier_type_code")
    id_type_display = _get(f"{prefix}_identifier_type_display") or _get("identifier_type_display")
    id_type_text = _get(f"{prefix}_identifier_type_text") or _get("identifier_type_text")
    id_type_user_selected = (
        _get(f"{prefix}_identifier_type_user_selected")
        if _get(f"{prefix}_identifier_type_user_selected") is not None
        else _get("identifier_type_user_selected")
    )
    id_system = _get(f"{prefix}_identifier_system") or _get("identifier_system")
    id_value = _get(f"{prefix}_identifier_value") or _get("identifier_value")
    id_period_start = _get(f"{prefix}_identifier_period_start") or _get("identifier_period_start")
    id_period_end = _get(f"{prefix}_identifier_period_end") or _get("identifier_period_end")

    if (
        id_use
        or id_type_system
        or id_type_version
        or id_type_code
        or id_type_display
        or id_type_text
        or (id_type_user_selected is not None)
        or id_system
        or id_value
        or id_period_start
        or id_period_end
    ):
        ident: dict = {}
        if id_use:
            ident["use"] = fhir_enum(id_use)
        if (
            id_type_system
            or id_type_version
            or id_type_code
            or id_type_display
            or id_type_text
            or (id_type_user_selected is not None)
        ):
            type_dict: dict = {}
            if (
                id_type_system
                or id_type_version
                or id_type_code
                or id_type_display
                or (id_type_user_selected is not None)
            ):
                coding_dict: dict = {}
                if id_type_system:
                    coding_dict["system"] = id_type_system
                if id_type_version:
                    coding_dict["version"] = id_type_version
                if id_type_code:
                    coding_dict["code"] = id_type_code
                if id_type_display:
                    coding_dict["display"] = id_type_display
                if id_type_user_selected is not None:
                    coding_dict["userSelected"] = id_type_user_selected
                type_dict["coding"] = [coding_dict]
            if id_type_text:
                type_dict["text"] = id_type_text
            ident["type"] = type_dict
        if id_system:
            ident["system"] = id_system
        if id_value:
            ident["value"] = id_value
        if id_period_start or id_period_end:
            p_dict: dict = {}
            if id_period_start:
                p_dict["start"] = (
                    id_period_start.isoformat()
                    if hasattr(id_period_start, "isoformat")
                    else str(id_period_start)
                )
            if id_period_end:
                p_dict["end"] = (
                    id_period_end.isoformat()
                    if hasattr(id_period_end, "isoformat")
                    else str(id_period_end)
                )
            ident["period"] = p_dict
        entry["identifier"] = ident

    return entry or None


def _child_reference_from_payload(item: Any) -> dict | None:
    if isinstance(item, str):
        return {"reference": item}
    return _reference_from_payload(item, "reference")


def _coding_from_payload(c) -> dict:
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


def _codeable_concept_from_payload(concept: DocumentReferenceCodeableConceptInput | None) -> dict | None:
    if not concept:
        return None
    codings = [_coding_from_payload(c) for c in (concept.coding or [])]
    codings = [c for c in codings if c]
    result: dict = {}
    if codings:
        result["coding"] = codings
    if concept.text:
        result["text"] = concept.text
    return result or None


def _identifier_from_payload(ident: DocumentReferenceIdentifierInput | None) -> dict | None:
    if not ident:
        return None
    entry: dict = {}
    if ident.use:
        entry["use"] = fhir_enum(ident.use)
    if ident.type_coding or ident.type_text:
        type_codings = [_coding_from_payload(c) for c in (ident.type_coding or [])]
        type_codings = [c for c in type_codings if c]
        type_dict: dict = {}
        if type_codings:
            type_dict["coding"] = type_codings
        if ident.type_text:
            type_dict["text"] = ident.type_text
        if type_dict:
            entry["type"] = type_dict
    if ident.system:
        entry["system"] = ident.system
    if ident.value:
        entry["value"] = ident.value
    if ident.period_start or ident.period_end:
        period: dict = {}
        if ident.period_start:
            period["start"] = ident.period_start.isoformat()
        if ident.period_end:
            period["end"] = ident.period_end.isoformat()
        entry["period"] = period
    assigner = _reference_from_payload(ident, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _content_from_payload(content: DocumentReferenceContentInput) -> dict:
    att = content.attachment
    attachment: dict = {}
    if getattr(att, "content_type", None):
        attachment["contentType"] = att.content_type
    if getattr(att, "language", None):
        attachment["language"] = att.language
    if getattr(att, "data", None):
        attachment["data"] = att.data
    if getattr(att, "url", None):
        attachment["url"] = att.url
    if getattr(att, "size", None) is not None:
        attachment["size"] = att.size
    if getattr(att, "hash", None):
        attachment["hash"] = att.hash
    if getattr(att, "title", None):
        attachment["title"] = att.title
    if getattr(att, "creation", None):
        attachment["creation"] = att.creation.isoformat() if hasattr(att.creation, "isoformat") else str(att.creation)

    entry: dict = {"attachment": attachment}
    if content.format:
        fmt = _coding_from_payload(content.format)
        if fmt:
            entry["format"] = fmt
    return entry


def _context_from_payload(context: DocumentReferenceContextInput | None) -> dict | None:
    if not context:
        return None
    ctx: dict = {}
    if context.encounter:
        ctx["encounter"] = [_child_reference_from_payload(e) for e in context.encounter if e]
    if context.event:
        events = [_codeable_concept_from_payload(e) for e in context.event]
        events = [e for e in events if e]
        if events:
            ctx["event"] = events
    if context.period_start or context.period_end:
        period: dict = {}
        if context.period_start:
            period["start"] = context.period_start.isoformat()
        if context.period_end:
            period["end"] = context.period_end.isoformat()
        ctx["period"] = period
    if context.facility_type:
        facility = _codeable_concept_from_payload(context.facility_type)
        if facility:
            ctx["facilityType"] = facility
    if context.practice_setting:
        practice = _codeable_concept_from_payload(context.practice_setting)
        if practice:
            ctx["practiceSetting"] = practice
    source_pat = _reference_from_payload(context, "source_patient_info")
    if source_pat:
        ctx["sourcePatientInfo"] = source_pat
    if context.related:
        ctx["related"] = [_child_reference_from_payload(r) for r in context.related if r]
    return ctx or None


_SUBJECT_FIELDS = {
    "subject",
    "subject_display",
    "subject_identifier_use",
    "subject_identifier_type_system",
    "subject_identifier_type_version",
    "subject_identifier_type_code",
    "subject_identifier_type_display",
    "subject_identifier_type_user_selected",
    "subject_identifier_type_text",
    "subject_identifier_system",
    "subject_identifier_value",
    "subject_identifier_period_start",
    "subject_identifier_period_end",
}

_AUTHENTICATOR_FIELDS = {
    "authenticator",
    "authenticator_display",
    "authenticator_identifier_use",
    "authenticator_identifier_type_system",
    "authenticator_identifier_type_version",
    "authenticator_identifier_type_code",
    "authenticator_identifier_type_display",
    "authenticator_identifier_type_user_selected",
    "authenticator_identifier_type_text",
    "authenticator_identifier_system",
    "authenticator_identifier_value",
    "authenticator_identifier_period_start",
    "authenticator_identifier_period_end",
}

_CUSTODIAN_FIELDS = {
    "custodian",
    "custodian_display",
    "custodian_identifier_use",
    "custodian_identifier_type_system",
    "custodian_identifier_type_version",
    "custodian_identifier_type_code",
    "custodian_identifier_type_display",
    "custodian_identifier_type_user_selected",
    "custodian_identifier_type_text",
    "custodian_identifier_system",
    "custodian_identifier_value",
    "custodian_identifier_period_start",
    "custodian_identifier_period_end",
}


def payload_to_fhir_document_reference(payload: DocumentReferenceCreateSchema) -> dict:
    """Map DocumentReferenceCreateSchema to a FHIR R4 DocumentReference dict for pre-write validation."""
    res: dict = {
        "resourceType": "DocumentReference",
    }

    if payload.master_identifier:
        mid = _identifier_from_payload(payload.master_identifier)
        if mid:
            res["masterIdentifier"] = mid

    if payload.identifier:
        ids = [_identifier_from_payload(i) for i in payload.identifier]
        ids = [i for i in ids if i]
        if ids:
            res["identifier"] = ids

    res["status"] = fhir_enum(payload.status)

    if payload.doc_status:
        res["docStatus"] = fhir_enum(payload.doc_status)

    if payload.type:
        type_cc = _codeable_concept_from_payload(payload.type)
        if type_cc:
            res["type"] = type_cc

    if payload.category:
        cats = [_codeable_concept_from_payload(c) for c in payload.category]
        cats = [c for c in cats if c]
        if cats:
            res["category"] = cats

    subj = _reference_from_payload(payload, "subject")
    if subj:
        res["subject"] = subj

    if payload.date:
        res["date"] = payload.date.isoformat()

    if payload.author:
        res["author"] = [_child_reference_from_payload(a) for a in payload.author if a]

    auth = _reference_from_payload(payload, "authenticator")
    if auth:
        res["authenticator"] = auth

    cust = _reference_from_payload(payload, "custodian")
    if cust:
        res["custodian"] = cust

    if payload.relates_to:
        rel_list = []
        for r in payload.relates_to:
            tgt = _reference_from_payload(r, "target")
            if tgt:
                rel_list.append({"code": fhir_enum(r.code), "target": tgt})
        if rel_list:
            res["relatesTo"] = rel_list

    if payload.description:
        res["description"] = payload.description

    if payload.security_label:
        secs = [_codeable_concept_from_payload(s) for s in payload.security_label]
        secs = [s for s in secs if s]
        if secs:
            res["securityLabel"] = secs

    if payload.content:
        res["content"] = [_content_from_payload(c) for c in payload.content]

    if payload.context:
        ctx = _context_from_payload(payload.context)
        if ctx:
            res["context"] = ctx

    return {k: v for k, v in res.items() if v is not None}


def patch_fragment_to_fhir_document_reference(
    payload: DocumentReferencePatchSchema,
) -> tuple[dict, set[str]]:
    """Map touched fields of DocumentReferencePatchSchema to a partial FHIR dict and set of touched keys."""
    touched: set[str] = set()
    fragment: dict = {}
    fields_set = payload.model_fields_set

    if "master_identifier" in fields_set:
        touched.add("masterIdentifier")
        if payload.master_identifier is not None:
            fragment["masterIdentifier"] = _identifier_from_payload(payload.master_identifier)

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                i for i in [_identifier_from_payload(x) for x in payload.identifier] if i
            ]

    if "status" in fields_set:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = fhir_enum(payload.status)

    if "doc_status" in fields_set:
        touched.add("docStatus")
        if payload.doc_status is not None:
            fragment["docStatus"] = fhir_enum(payload.doc_status)

    if "type" in fields_set:
        touched.add("type")
        if payload.type is not None:
            fragment["type"] = _codeable_concept_from_payload(payload.type)

    if "category" in fields_set:
        touched.add("category")
        if payload.category is not None:
            fragment["category"] = [
                c for c in [_codeable_concept_from_payload(x) for x in payload.category] if c
            ]

    if fields_set & _SUBJECT_FIELDS:
        touched.add("subject")
        subj = _reference_from_payload(payload, "subject")
        if subj:
            fragment["subject"] = subj

    if "date" in fields_set:
        touched.add("date")
        if payload.date is not None:
            fragment["date"] = payload.date.isoformat()

    if "author" in fields_set:
        touched.add("author")
        if payload.author is not None:
            fragment["author"] = [_child_reference_from_payload(a) for a in payload.author if a]

    if fields_set & _AUTHENTICATOR_FIELDS:
        touched.add("authenticator")
        auth = _reference_from_payload(payload, "authenticator")
        if auth:
            fragment["authenticator"] = auth

    if fields_set & _CUSTODIAN_FIELDS:
        touched.add("custodian")
        cust = _reference_from_payload(payload, "custodian")
        if cust:
            fragment["custodian"] = cust

    if "relates_to" in fields_set:
        touched.add("relatesTo")
        if payload.relates_to is not None:
            rel_list = []
            for r in payload.relates_to:
                tgt = _reference_from_payload(r, "target")
                if tgt:
                    rel_list.append({"code": fhir_enum(r.code), "target": tgt})
            fragment["relatesTo"] = rel_list

    if "description" in fields_set:
        touched.add("description")
        if payload.description is not None:
            fragment["description"] = payload.description

    if "security_label" in fields_set:
        touched.add("securityLabel")
        if payload.security_label is not None:
            fragment["securityLabel"] = [
                s for s in [_codeable_concept_from_payload(x) for x in payload.security_label] if s
            ]

    if "content" in fields_set:
        touched.add("content")
        if payload.content is not None:
            fragment["content"] = [_content_from_payload(c) for c in payload.content]

    if "context" in fields_set:
        touched.add("context")
        if payload.context is not None:
            fragment["context"] = _context_from_payload(payload.context)

    return fragment, touched
