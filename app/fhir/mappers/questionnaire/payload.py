"""Payload -> FHIR JSON conversion, the mirror image of fhir.py — see that
module's docstring pattern (e.g. app.fhir.mappers.organization.payload) for
the full reasoning. Reads the validated Pydantic input schema
(QuestionnaireCreateSchema / QuestionnairePatchSchema and their nested
item/sub-resource schemas) rather than the persisted ORM model, before
anything is written to the DB.

Every choice-type enum field here (operator, item type, quantity
comparator) is a *schema-layer* Pydantic enum whose `.value` IS the real
FHIR wire string (e.g. QuestionnaireItemOperator.eq.value == "=",
QuestionnaireItemType.open_choice.value == "open-choice") — unlike fhir.py,
which reads the *model-layer* enum (readable name == value) and has to
look the real symbol up in a dict. No such lookup is needed here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.questionnaire.input import (
        QuestionnaireContactInput,
        QuestionnaireCreateSchema,
        QuestionnaireIdentifierInput,
        QuestionnaireItemAnswerOptionInput,
        QuestionnaireItemEnableWhenInput,
        QuestionnaireItemInitialInput,
        QuestionnaireItemInput,
        QuestionnaireJurisdictionInput,
        QuestionnairePatchSchema,
        QuestionnaireUseContextInput,
    )


def _coding_list(codings) -> list[dict]:
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


def _reference_from_payload(obj, prefix: str) -> dict:
    raw_reference = getattr(obj, prefix, None)
    display = getattr(obj, f"{prefix}_display", None)
    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    if display:
        entry["display"] = display
    return entry


def _reference_with_identifier_fallback_from_payload(obj, prefix: str) -> dict:
    entry = _reference_from_payload(obj, prefix)

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


def _quantity_from_payload(obj, prefix: str) -> dict:
    value = getattr(obj, f"{prefix}_value", None)
    comparator = getattr(obj, f"{prefix}_comparator", None)
    return {
        k: v
        for k, v in {
            "value": value,
            "comparator": comparator.value if comparator else None,
            "unit": getattr(obj, f"{prefix}_unit", None),
            "system": getattr(obj, f"{prefix}_system", None),
            "code": getattr(obj, f"{prefix}_code", None),
        }.items()
        if v is not None
    }


def payload_questionnaire_identifier(i: QuestionnaireIdentifierInput) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = i.use.value
    coding = _coding_list(i.type_coding)
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
    assigner = _reference_with_identifier_fallback_from_payload(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def payload_questionnaire_contact(c: QuestionnaireContactInput) -> dict:
    entry: dict = {}
    if c.name:
        entry["name"] = c.name
    if c.telecom:
        telecoms = []
        for t in c.telecom:
            tel: dict = {}
            if t.system:
                tel["system"] = t.system.value
            if t.value:
                tel["value"] = t.value
            if t.use:
                tel["use"] = t.use.value
            if t.rank is not None:
                tel["rank"] = t.rank
            period = _period(t.period_start, t.period_end)
            if period:
                tel["period"] = period
            telecoms.append(tel)
        if telecoms:
            entry["telecom"] = telecoms
    return entry


def payload_questionnaire_jurisdiction(j: QuestionnaireJurisdictionInput) -> dict:
    entry: dict = {}
    coding = _coding_list(j.coding)
    if coding:
        entry["coding"] = coding
    if j.text:
        entry["text"] = j.text
    return entry


def payload_questionnaire_use_context(uc: QuestionnaireUseContextInput) -> dict:
    entry: dict = {
        "code": {
            k: v
            for k, v in {
                "system": uc.code_system,
                "version": uc.code_version,
                "code": uc.code_code,
                "display": uc.code_display,
                "userSelected": uc.code_user_selected,
            }.items()
            if v is not None
        }
    }

    if uc.value_codeable_concept_text or uc.value_codeable_concept_coding:
        cc: dict = {}
        coding = _coding_list(uc.value_codeable_concept_coding)
        if coding:
            cc["coding"] = coding
        if uc.value_codeable_concept_text:
            cc["text"] = uc.value_codeable_concept_text
        entry["valueCodeableConcept"] = cc
    elif uc.value_quantity_value is not None or uc.value_quantity_unit or uc.value_quantity_system or uc.value_quantity_code:
        entry["valueQuantity"] = _quantity_from_payload(uc, "value_quantity")
    elif uc.value_range_low_value is not None or uc.value_range_high_value is not None:
        rng: dict = {}
        low = _quantity_from_payload(uc, "value_range_low")
        high = _quantity_from_payload(uc, "value_range_high")
        if low:
            rng["low"] = low
        if high:
            rng["high"] = high
        entry["valueRange"] = rng
    elif uc.value_reference:
        ref = _reference_from_payload(uc, "value_reference")
        if ref:
            entry["valueReference"] = ref

    return entry


def payload_questionnaire_item_enable_when(ew: QuestionnaireItemEnableWhenInput) -> dict:
    entry: dict = {"question": ew.question, "operator": ew.operator.value}

    if ew.answer_boolean is not None:
        entry["answerBoolean"] = ew.answer_boolean
    elif ew.answer_decimal is not None:
        entry["answerDecimal"] = ew.answer_decimal
    elif ew.answer_integer is not None:
        entry["answerInteger"] = ew.answer_integer
    elif ew.answer_date is not None:
        entry["answerDate"] = ew.answer_date.isoformat()
    elif ew.answer_date_time is not None:
        entry["answerDateTime"] = ew.answer_date_time.isoformat()
    elif ew.answer_time is not None:
        entry["answerTime"] = ew.answer_time.isoformat()
    elif ew.answer_string is not None:
        entry["answerString"] = ew.answer_string
    elif ew.answer_coding_system or ew.answer_coding_code:
        entry["answerCoding"] = {
            k: v
            for k, v in {
                "system": ew.answer_coding_system,
                "version": ew.answer_coding_version,
                "code": ew.answer_coding_code,
                "display": ew.answer_coding_display,
                "userSelected": ew.answer_coding_user_selected,
            }.items()
            if v is not None
        }
    elif ew.answer_quantity_value is not None or ew.answer_quantity_unit or ew.answer_quantity_system or ew.answer_quantity_code:
        entry["answerQuantity"] = _quantity_from_payload(ew, "answer_quantity")
    elif ew.answer_reference:
        ref = _reference_from_payload(ew, "answer_reference")
        if ref:
            entry["answerReference"] = ref

    return entry


def payload_questionnaire_item_answer_option(ao: QuestionnaireItemAnswerOptionInput) -> dict:
    entry: dict = {}

    if ao.value_integer is not None:
        entry["valueInteger"] = ao.value_integer
    elif ao.value_date is not None:
        entry["valueDate"] = ao.value_date.isoformat()
    elif ao.value_time is not None:
        entry["valueTime"] = ao.value_time.isoformat()
    elif ao.value_string is not None:
        entry["valueString"] = ao.value_string
    elif ao.value_coding_system or ao.value_coding_code:
        entry["valueCoding"] = {
            k: v
            for k, v in {
                "system": ao.value_coding_system,
                "version": ao.value_coding_version,
                "code": ao.value_coding_code,
                "display": ao.value_coding_display,
                "userSelected": ao.value_coding_user_selected,
            }.items()
            if v is not None
        }
    elif ao.value_reference:
        ref = _reference_from_payload(ao, "value_reference")
        if ref:
            entry["valueReference"] = ref

    if ao.initial_selected is not None:
        entry["initialSelected"] = ao.initial_selected

    return entry


def payload_questionnaire_item_initial(ini: QuestionnaireItemInitialInput) -> dict:
    entry: dict = {}

    if ini.value_boolean is not None:
        entry["valueBoolean"] = ini.value_boolean
    elif ini.value_decimal is not None:
        entry["valueDecimal"] = ini.value_decimal
    elif ini.value_integer is not None:
        entry["valueInteger"] = ini.value_integer
    elif ini.value_date is not None:
        entry["valueDate"] = ini.value_date.isoformat()
    elif ini.value_date_time is not None:
        entry["valueDateTime"] = ini.value_date_time.isoformat()
    elif ini.value_time is not None:
        entry["valueTime"] = ini.value_time.isoformat()
    elif ini.value_string is not None:
        entry["valueString"] = ini.value_string
    elif ini.value_uri is not None:
        entry["valueUri"] = ini.value_uri
    elif ini.value_attachment is not None:
        a = ini.value_attachment
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
                "creation": a.creation.isoformat() if a.creation else None,
            }.items()
            if v is not None
        }
    elif ini.value_coding_system or ini.value_coding_code:
        entry["valueCoding"] = {
            k: v
            for k, v in {
                "system": ini.value_coding_system,
                "version": ini.value_coding_version,
                "code": ini.value_coding_code,
                "display": ini.value_coding_display,
                "userSelected": ini.value_coding_user_selected,
            }.items()
            if v is not None
        }
    elif ini.value_quantity_value is not None or ini.value_quantity_unit or ini.value_quantity_system or ini.value_quantity_code:
        entry["valueQuantity"] = _quantity_from_payload(ini, "value_quantity")
    elif ini.value_reference:
        ref = _reference_from_payload(ini, "value_reference")
        if ref:
            entry["valueReference"] = ref

    return entry


def payload_questionnaire_item(item: QuestionnaireItemInput) -> dict:
    """Recursive — mirrors QuestionnaireItemInput's own `item: list[...]`
    self-reference."""
    entry: dict = {"linkId": item.link_id, "type": item.type.value}

    if item.definition:
        entry["definition"] = item.definition
    coding = _coding_list(item.code)
    if coding:
        entry["code"] = coding
    if item.prefix:
        entry["prefix"] = item.prefix
    if item.text:
        entry["text"] = item.text
    if item.enable_when:
        entry["enableWhen"] = [payload_questionnaire_item_enable_when(ew) for ew in item.enable_when]
    if item.enable_behavior:
        entry["enableBehavior"] = item.enable_behavior.value
    if item.required is not None:
        entry["required"] = item.required
    if item.repeats is not None:
        entry["repeats"] = item.repeats
    if item.read_only is not None:
        entry["readOnly"] = item.read_only
    if item.max_length is not None:
        entry["maxLength"] = item.max_length
    if item.answer_value_set:
        entry["answerValueSet"] = item.answer_value_set
    if item.answer_option:
        entry["answerOption"] = [payload_questionnaire_item_answer_option(ao) for ao in item.answer_option]
    if item.initial:
        entry["initial"] = [payload_questionnaire_item_initial(ini) for ini in item.initial]
    if item.item:
        entry["item"] = [payload_questionnaire_item(child) for child in item.item]

    return entry


# Shared by both orchestrators below.
_LIST_FIELDS = {
    "identifier": payload_questionnaire_identifier,
    "contact": payload_questionnaire_contact,
    "use_context": payload_questionnaire_use_context,
    "jurisdiction": payload_questionnaire_jurisdiction,
}

_FHIR_KEY_FOR_FIELD = {
    "identifier": "identifier",
    "contact": "contact",
    "use_context": "useContext",
    "jurisdiction": "jurisdiction",
}


def payload_to_fhir_questionnaire(payload: QuestionnaireCreateSchema) -> dict:
    """Full-resource conversion for CREATE: every field is considered
    present — unlike patch_fragment_to_fhir_questionnaire()'s tri-state
    handling."""
    result: dict = {"resourceType": "Questionnaire"}

    if payload.extension:
        result["extension"] = list(payload.extension)
    if payload.url:
        result["url"] = payload.url
    if payload.version:
        result["version"] = payload.version
    if payload.name:
        result["name"] = payload.name
    if payload.title:
        result["title"] = payload.title
    if payload.derived_from:
        result["derivedFrom"] = list(payload.derived_from)
    if payload.status:
        result["status"] = payload.status.value
    if payload.experimental is not None:
        result["experimental"] = payload.experimental
    if payload.subject_type:
        result["subjectType"] = list(payload.subject_type)
    if payload.date:
        result["date"] = payload.date.isoformat()
    if payload.publisher:
        result["publisher"] = payload.publisher
    if payload.description:
        result["description"] = payload.description
    if payload.purpose:
        result["purpose"] = payload.purpose
    if payload.copyright:
        result["copyright"] = payload.copyright
    if payload.approval_date:
        result["approvalDate"] = payload.approval_date.isoformat()
    if payload.last_review_date:
        result["lastReviewDate"] = payload.last_review_date.isoformat()
    period = _period(payload.effective_period_start, payload.effective_period_end)
    if period:
        result["effectivePeriod"] = period

    coding = _coding_list(payload.code)
    if coding:
        result["code"] = coding

    for field, builder in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        if items:
            result[_FHIR_KEY_FOR_FIELD[field]] = items

    if payload.item:
        result["item"] = [payload_questionnaire_item(item) for item in payload.item]

    return result


def patch_fragment_to_fhir_questionnaire(
    payload: QuestionnairePatchSchema,
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
    if "url" in provided:
        touched.add("url")
        if payload.url:
            fragment["url"] = payload.url
    if "version" in provided:
        touched.add("version")
        if payload.version:
            fragment["version"] = payload.version
    if "name" in provided:
        touched.add("name")
        if payload.name:
            fragment["name"] = payload.name
    if "title" in provided:
        touched.add("title")
        if payload.title:
            fragment["title"] = payload.title
    if "derived_from" in provided:
        touched.add("derivedFrom")
        if payload.derived_from:
            fragment["derivedFrom"] = list(payload.derived_from)
    if "status" in provided:
        touched.add("status")
        if payload.status:
            fragment["status"] = payload.status.value
    if "experimental" in provided:
        touched.add("experimental")
        if payload.experimental is not None:
            fragment["experimental"] = payload.experimental
    if "subject_type" in provided:
        touched.add("subjectType")
        if payload.subject_type:
            fragment["subjectType"] = list(payload.subject_type)
    if "date" in provided:
        touched.add("date")
        if payload.date:
            fragment["date"] = payload.date.isoformat()
    if "publisher" in provided:
        touched.add("publisher")
        if payload.publisher:
            fragment["publisher"] = payload.publisher
    if "description" in provided:
        touched.add("description")
        if payload.description:
            fragment["description"] = payload.description
    if "purpose" in provided:
        touched.add("purpose")
        if payload.purpose:
            fragment["purpose"] = payload.purpose
    if "copyright" in provided:
        touched.add("copyright")
        if payload.copyright:
            fragment["copyright"] = payload.copyright
    if "approval_date" in provided:
        touched.add("approvalDate")
        if payload.approval_date:
            fragment["approvalDate"] = payload.approval_date.isoformat()
    if "last_review_date" in provided:
        touched.add("lastReviewDate")
        if payload.last_review_date:
            fragment["lastReviewDate"] = payload.last_review_date.isoformat()
    if provided & {"effective_period_start", "effective_period_end"}:
        touched.add("effectivePeriod")
        period = _period(payload.effective_period_start, payload.effective_period_end)
        if period:
            fragment["effectivePeriod"] = period
    if "code" in provided:
        touched.add("code")
        coding = _coding_list(payload.code)
        if coding:
            fragment["code"] = coding

    for field, builder in _LIST_FIELDS.items():
        if field in provided:
            touched.add(_FHIR_KEY_FOR_FIELD[field])
            items = [builder(item) for item in (getattr(payload, field, None) or [])]
            if items:
                fragment[_FHIR_KEY_FOR_FIELD[field]] = items

    if "item" in provided:
        touched.add("item")
        if payload.item:
            fragment["item"] = [payload_questionnaire_item(item) for item in payload.item]

    return fragment, touched
