from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.questionnaire_response import (
        QuestionnaireResponseAnswer,
        QuestionnaireResponseItem,
        QuestionnaireResponseModel,
    )

_COMPARATOR_SYMBOLS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict from `{prefix}_reference`/`{prefix}_type`/
    `{prefix}_id`/`{prefix}_display`. Resource-scoped copy — mirrors
    app.fhir.mappers.questionnaire.fhir._fhir_reference field-for-field."""
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
    return entry


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict:
    """Same as `_fhir_reference`, plus the `{prefix}_identifier_*`
    logical-reference fallback — used for every dedicated Reference field
    on this resource (subject/encounter/author/source, plus basedOn/
    partOf's own rows)."""
    entry = _fhir_reference(obj, prefix)

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
                for k, v in {
                    "start": fhir_instant(id_period_start),
                    "end": fhir_instant(id_period_end),
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def _fhir_quantity(obj, prefix: str) -> dict:
    value = getattr(obj, f"{prefix}_value", None)
    comparator = getattr(obj, f"{prefix}_comparator", None)
    return {
        k: v
        for k, v in {
            "value": float(value) if value is not None else None,
            "comparator": _COMPARATOR_SYMBOLS.get(fhir_enum(comparator)) if comparator else None,
            "unit": getattr(obj, f"{prefix}_unit", None),
            "system": getattr(obj, f"{prefix}_system", None),
            "code": getattr(obj, f"{prefix}_code", None),
        }.items()
        if v is not None
    }


def fhir_questionnaire_response_identifier(qr: QuestionnaireResponseModel) -> dict:
    """QuestionnaireResponse.identifier (0..1) — flattened directly onto
    the main row; `.type.coding[]` comes from the real
    `identifier_type_codings` child-table relationship regardless."""
    entry: dict = {}
    if qr.identifier_use:
        entry["use"] = fhir_enum(qr.identifier_use)
    coding = [
        {
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
        for c in (qr.identifier_type_codings or [])
    ]
    coding = [c for c in coding if c]
    if coding or qr.identifier_type_text:
        type_cc: dict = {}
        if coding:
            type_cc["coding"] = coding
        if qr.identifier_type_text:
            type_cc["text"] = qr.identifier_type_text
        entry["type"] = type_cc
    if qr.identifier_system:
        entry["system"] = qr.identifier_system
    if qr.identifier_value:
        entry["value"] = qr.identifier_value
    if qr.identifier_period_start or qr.identifier_period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(qr.identifier_period_start),
                "end": fhir_instant(qr.identifier_period_end),
            }.items()
            if v
        }
    assigner = _fhir_reference_with_identifier_fallback(qr, "identifier_assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def _fhir_answer_value(a: QuestionnaireResponseAnswer) -> dict:
    entry: dict = {}
    if a.value_boolean is not None:
        entry["valueBoolean"] = a.value_boolean
    elif a.value_decimal is not None:
        entry["valueDecimal"] = float(a.value_decimal)
    elif a.value_integer is not None:
        entry["valueInteger"] = a.value_integer
    elif a.value_date is not None:
        entry["valueDate"] = a.value_date.isoformat()
    elif a.value_date_time is not None:
        entry["valueDateTime"] = fhir_instant(a.value_date_time)
    elif a.value_time is not None:
        entry["valueTime"] = a.value_time.isoformat()
    elif a.value_string is not None:
        entry["valueString"] = a.value_string
    elif a.value_uri is not None:
        entry["valueUri"] = a.value_uri
    elif a.content_type or a.url or a.data or a.title:
        # FhirAttachmentMixin's bare attribute names — _attachment_prefix
        # ("value_attachment_") only renames the DB column.
        entry["valueAttachment"] = {
            k: v
            for k, v in {
                "contentType": a.content_type,
                "language": a.language,
                "data": a.data,
                "url": a.url,
                "size": a.size,
                "hash": a.hash,
                "title": a.title,
                "creation": fhir_instant(a.creation),
            }.items()
            if v is not None
        }
    elif a.system or a.code:
        # FhirCodingMixin's bare attribute names.
        entry["valueCoding"] = {
            k: v
            for k, v in {
                "system": a.system,
                "version": a.version,
                "code": a.code,
                "display": a.display,
                "userSelected": a.user_selected,
            }.items()
            if v is not None
        }
    elif a.value_quantity_value is not None or a.value_quantity_unit or a.value_quantity_system or a.value_quantity_code:
        entry["valueQuantity"] = _fhir_quantity(a, "value_quantity")
    elif a.value_reference_reference or (a.value_reference_type and a.value_reference_id):
        ref = _fhir_reference(a, "value_reference")
        if ref:
            entry["valueReference"] = ref

    return entry


def _build_response_item_tree(
    items: list[QuestionnaireResponseItem], answers: list[QuestionnaireResponseAnswer]
) -> list[dict]:
    """Reconstructs the nested FHIR `item[]`/`answer[].item[]` shape from
    the flat, eager-loaded `items`/`answers` collections (every row at
    every depth — see QuestionnaireResponseModel's docstring) by grouping
    items on BOTH `parent_item_id` and `parent_answer_id`, and answers on
    `item_id` — O(n), no recursive queries. A given item is grouped under
    exactly one of the two item dicts, per the FHIR invariant that its
    children live under item.item XOR under one of its answers' item[]."""
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
        entry = _fhir_answer_value(answer)
        children = render_items(items_by_parent_answer.get(answer.id, []))
        if children:
            entry["item"] = children
        return entry

    def render_items(item_list: list) -> list[dict]:
        result = []
        for item in item_list:
            entry: dict = {"linkId": item.link_id}
            if item.definition:
                entry["definition"] = item.definition
            if item.text:
                entry["text"] = item.text
            answer_entries = [render_answer(a) for a in answers_by_item.get(item.id, [])]
            if answer_entries:
                entry["answer"] = answer_entries
            children = render_items(items_by_parent_item.get(item.id, []))
            if children:
                entry["item"] = children
            result.append(entry)
        return result

    return render_items(items_by_parent_item.get(None, []))


# Base URL for this server's own, not-yet-formally-registered extensions —
# same convention as every other resource's _fhir_meta.
_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(qr: QuestionnaireResponseModel) -> dict:
    """TenantAuditMixin's columns rendered into Resource.meta — mirrors
    app.fhir.mappers.questionnaire.fhir._fhir_meta."""
    meta: dict = {}
    if qr.updated_at:
        meta["lastUpdated"] = fhir_instant(qr.updated_at)

    extensions = []
    if qr.tenant_id:
        extensions.append({"url": f"{_EXT_BASE}/org-id", "valueString": qr.tenant_id})
    if qr.created_by:
        extensions.append({"url": f"{_EXT_BASE}/created-by", "valueString": qr.created_by})
    if qr.updated_by:
        extensions.append({"url": f"{_EXT_BASE}/updated-by", "valueString": qr.updated_by})
    if qr.created_at:
        extensions.append({"url": f"{_EXT_BASE}/created-at", "valueDateTime": fhir_instant(qr.created_at)})
    if extensions:
        meta["extension"] = extensions

    return meta


def to_fhir_questionnaire_response(qr: QuestionnaireResponseModel) -> dict:
    result: dict = {
        "resourceType": "QuestionnaireResponse",
        "id": str(qr.questionnaire_response_id),
    }

    meta = _fhir_meta(qr)
    if meta:
        result["meta"] = meta

    if qr.extension:
        result["extension"] = list(qr.extension)

    identifier = fhir_questionnaire_response_identifier(qr)
    if identifier:
        result["identifier"] = identifier

    based_ons = [_fhir_reference_with_identifier_fallback(b, "reference") for b in (qr.based_ons or [])]
    based_ons = [b for b in based_ons if b]
    if based_ons:
        result["basedOn"] = based_ons

    part_ofs = [_fhir_reference_with_identifier_fallback(p, "reference") for p in (qr.part_ofs or [])]
    part_ofs = [p for p in part_ofs if p]
    if part_ofs:
        result["partOf"] = part_ofs

    if qr.questionnaire:
        result["questionnaire"] = qr.questionnaire

    if qr.status:
        result["status"] = fhir_enum(qr.status).replace("_", "-")

    subject = _fhir_reference_with_identifier_fallback(qr, "subject")
    if subject:
        result["subject"] = subject

    encounter = _fhir_reference_with_identifier_fallback(qr, "encounter")
    if encounter:
        result["encounter"] = encounter

    if qr.authored:
        result["authored"] = fhir_instant(qr.authored)

    author = _fhir_reference_with_identifier_fallback(qr, "author")
    if author:
        result["author"] = author

    source = _fhir_reference_with_identifier_fallback(qr, "source")
    if source:
        result["source"] = source

    items = _build_response_item_tree(qr.items or [], qr.answers or [])
    if items:
        result["item"] = items

    return {k: v for k, v in result.items() if v is not None}
