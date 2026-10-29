"""Payload -> FHIR JSON conversion, the mirror image of fhir.py — see that
module's docstring pattern (e.g. app.fhir.mappers.organization.payload) for
the full reasoning. Reads the validated Pydantic input schema
(QuestionnaireResponseCreateSchema / QuestionnaireResponsePatchSchema and
their nested item/answer/reference schemas) rather than the persisted ORM
model, before anything is written to the DB.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.questionnaire_response.input import (
        QuestionnaireResponseAnswerInput,
        QuestionnaireResponseCreateSchema,
        QuestionnaireResponseIdentifierInput,
        QuestionnaireResponseItemInput,
        QuestionnaireResponsePatchSchema,
    )


def _period(start, end) -> dict | None:
    period = {
        k: v
        for k, v in {
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
        }.items()
        if v
    }
    return period or None


def _reference_from_payload(obj, prefix: str = "reference") -> dict:
    """`obj` is one of the `_ReferenceListInput`/`_SingleReferenceInput`
    nested schema objects — the raw reference string lives on its own
    `reference` attribute (bare, not `{prefix}_reference`, since the
    whole object IS the reference), per
    app.schemas.questionnaire_response.input.reference's shape."""
    raw_reference = getattr(obj, "reference", None)
    display = getattr(obj, "reference_display", None)
    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    if display:
        entry["display"] = display
    return entry


def _reference_with_identifier_fallback_from_payload(obj) -> dict:
    entry = _reference_from_payload(obj)

    id_use = getattr(obj, "reference_identifier_use", None)
    id_type_system = getattr(obj, "reference_identifier_type_system", None)
    id_type_version = getattr(obj, "reference_identifier_type_version", None)
    id_type_code = getattr(obj, "reference_identifier_type_code", None)
    id_type_display = getattr(obj, "reference_identifier_type_display", None)
    id_type_text = getattr(obj, "reference_identifier_type_text", None)
    id_type_user_selected = getattr(obj, "reference_identifier_type_user_selected", None)
    id_system = getattr(obj, "reference_identifier_system", None)
    id_value = getattr(obj, "reference_identifier_value", None)
    id_period_start = getattr(obj, "reference_identifier_period_start", None)
    id_period_end = getattr(obj, "reference_identifier_period_end", None)

    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
        identifier: dict = {}
        if id_use:
            identifier["use"] = id_use.value if hasattr(id_use, "value") else id_use
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
        period = _period(id_period_start, id_period_end)
        if period:
            identifier["period"] = period
        entry["identifier"] = identifier
    return entry


def payload_questionnaire_response_identifier(i: QuestionnaireResponseIdentifierInput) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = i.use.value
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
        for c in (i.type_coding or [])
    ]
    coding = [c for c in coding if c]
    if coding or i.type_text:
        type_cc: dict = {}
        if coding:
            type_cc["coding"] = coding
        if i.type_text:
            type_cc["text"] = i.type_text
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    period = _period(i.period_start, i.period_end)
    if period:
        entry["period"] = period
    if i.assigner:
        assigner: dict = {"reference": i.assigner}
        if i.assigner_display:
            assigner["display"] = i.assigner_display
        entry["assigner"] = assigner
    return entry


def payload_questionnaire_response_answer(a: QuestionnaireResponseAnswerInput) -> dict:
    entry: dict = {}

    if a.value_boolean is not None:
        entry["valueBoolean"] = a.value_boolean
    elif a.value_decimal is not None:
        entry["valueDecimal"] = a.value_decimal
    elif a.value_integer is not None:
        entry["valueInteger"] = a.value_integer
    elif a.value_date is not None:
        entry["valueDate"] = a.value_date.isoformat()
    elif a.value_date_time is not None:
        entry["valueDateTime"] = a.value_date_time.isoformat()
    elif a.value_time is not None:
        entry["valueTime"] = a.value_time.isoformat()
    elif a.value_string is not None:
        entry["valueString"] = a.value_string
    elif a.value_uri is not None:
        entry["valueUri"] = a.value_uri
    elif a.value_attachment is not None:
        at = a.value_attachment
        entry["valueAttachment"] = {
            k: v
            for k, v in {
                "contentType": at.content_type,
                "language": at.language,
                "data": at.data,
                "url": at.url,
                "size": at.size,
                "hash": at.hash,
                "title": at.title,
                "creation": at.creation.isoformat() if at.creation else None,
            }.items()
            if v is not None
        }
    elif a.value_coding_system or a.value_coding_code:
        entry["valueCoding"] = {
            k: v
            for k, v in {
                "system": a.value_coding_system,
                "version": a.value_coding_version,
                "code": a.value_coding_code,
                "display": a.value_coding_display,
                "userSelected": a.value_coding_user_selected,
            }.items()
            if v is not None
        }
    elif a.value_quantity_value is not None or a.value_quantity_unit or a.value_quantity_system or a.value_quantity_code:
        entry["valueQuantity"] = {
            k: v
            for k, v in {
                "value": a.value_quantity_value,
                "comparator": a.value_quantity_comparator.value if a.value_quantity_comparator else None,
                "unit": a.value_quantity_unit,
                "system": a.value_quantity_system,
                "code": a.value_quantity_code,
            }.items()
            if v is not None
        }
    elif a.value_reference:
        ref: dict = {"reference": a.value_reference}
        if a.value_reference_display:
            ref["display"] = a.value_reference_display
        entry["valueReference"] = ref

    if a.item:
        entry["item"] = [payload_questionnaire_response_item(child) for child in a.item]

    return entry


def payload_questionnaire_response_item(item: QuestionnaireResponseItemInput) -> dict:
    """Recursive — mirrors QuestionnaireResponseItemInput's own `item:
    list[...]` self-reference."""
    entry: dict = {"linkId": item.link_id}

    if item.definition:
        entry["definition"] = item.definition
    if item.text:
        entry["text"] = item.text
    if item.answer:
        entry["answer"] = [payload_questionnaire_response_answer(a) for a in item.answer]
    if item.item:
        entry["item"] = [payload_questionnaire_response_item(child) for child in item.item]

    return entry


# Shared by both orchestrators below.
_SINGLE_REFERENCE_FIELDS = {
    "subject": "subject",
    "encounter": "encounter",
    "author": "author",
    "source": "source",
}
_LIST_REFERENCE_FIELDS = {
    "based_on": "basedOn",
    "part_of": "partOf",
}


def payload_to_fhir_questionnaire_response(payload: QuestionnaireResponseCreateSchema) -> dict:
    """Full-resource conversion for CREATE: every field is considered
    present — unlike patch_fragment_to_fhir_questionnaire_response()'s
    tri-state handling."""
    result: dict = {"resourceType": "QuestionnaireResponse"}

    if payload.extension:
        result["extension"] = list(payload.extension)
    if payload.identifier:
        identifier = payload_questionnaire_response_identifier(payload.identifier)
        if identifier:
            result["identifier"] = identifier

    for field, fhir_key in _LIST_REFERENCE_FIELDS.items():
        items = [_reference_with_identifier_fallback_from_payload(r) for r in (getattr(payload, field, None) or [])]
        items = [r for r in items if r]
        if items:
            result[fhir_key] = items

    if payload.questionnaire:
        result["questionnaire"] = payload.questionnaire
    if payload.status:
        result["status"] = payload.status.value

    for field, fhir_key in _SINGLE_REFERENCE_FIELDS.items():
        obj = getattr(payload, field, None)
        if obj:
            ref = _reference_with_identifier_fallback_from_payload(obj)
            if ref:
                result[fhir_key] = ref

    if payload.authored:
        result["authored"] = payload.authored.isoformat()

    if payload.item:
        result["item"] = [payload_questionnaire_response_item(item) for item in payload.item]

    return result


def patch_fragment_to_fhir_questionnaire_response(
    payload: QuestionnaireResponsePatchSchema,
) -> tuple[dict, set[str]]:
    """Tri-state conversion for PATCH — see
    app.fhir.mappers.organization.payload.patch_fragment_to_fhir_organization's
    docstring for the full reasoning (identical shape, resource-specific
    field set here)."""
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = list(payload.extension)

    if "identifier" in provided:
        touched.add("identifier")
        if payload.identifier:
            identifier = payload_questionnaire_response_identifier(payload.identifier)
            if identifier:
                fragment["identifier"] = identifier

    for field, fhir_key in _LIST_REFERENCE_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            items = [
                _reference_with_identifier_fallback_from_payload(r) for r in (getattr(payload, field, None) or [])
            ]
            items = [r for r in items if r]
            if items:
                fragment[fhir_key] = items

    if "questionnaire" in provided:
        touched.add("questionnaire")
        if payload.questionnaire:
            fragment["questionnaire"] = payload.questionnaire
    if "status" in provided:
        touched.add("status")
        if payload.status:
            fragment["status"] = payload.status.value

    for field, fhir_key in _SINGLE_REFERENCE_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            obj = getattr(payload, field, None)
            if obj:
                ref = _reference_with_identifier_fallback_from_payload(obj)
                if ref:
                    fragment[fhir_key] = ref

    if "authored" in provided:
        touched.add("authored")
        if payload.authored:
            fragment["authored"] = payload.authored.isoformat()

    if "item" in provided:
        touched.add("item")
        if payload.item:
            fragment["item"] = [payload_questionnaire_response_item(item) for item in payload.item]

    return fragment, touched
