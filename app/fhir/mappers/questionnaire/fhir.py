from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant, fhir_telecom

if TYPE_CHECKING:
    from app.models.questionnaire import (
        QuestionnaireContact,
        QuestionnaireIdentifier,
        QuestionnaireItem,
        QuestionnaireItemAnswerOption,
        QuestionnaireItemEnableWhen,
        QuestionnaireItemInitial,
        QuestionnaireJurisdiction,
        QuestionnaireModel,
        QuestionnaireUseContext,
    )

_COMPARATOR_SYMBOLS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}
_OPERATOR_SYMBOLS = {"exists": "exists", "eq": "=", "ne": "!=", "gt": ">", "lt": "<", "ge": ">=", "le": "<="}


def _fhir_coding_list(codings) -> list[dict]:
    """Render a list of FhirCodingMixin-shaped rows as a FHIR `coding[]`
    array. Shared by every Questionnaire CodeableConcept-coding list."""
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


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict from `{prefix}_reference`/`{prefix}_type`/
    `{prefix}_id`/`{prefix}_display`, plus the `{prefix}_identifier_*`
    logical-reference fallback. Mirrors
    app.fhir.mappers.organization.fhir._fhir_reference — reused shape, not
    the same function, since Questionnaire's own reference fields (assigner,
    useContext.valueReference) don't all carry an identifier fallback."""
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
    """Same as _fhir_reference, plus the `{prefix}_identifier_*` logical-
    reference fallback — used for Questionnaire.identifier.assigner (a
    Reference(Organization) that always carries the fallback, per every
    other resource's own Identifier.assigner handling)."""
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


def fhir_questionnaire_identifier(i: QuestionnaireIdentifier) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    coding = _fhir_coding_list(i.type_codings)
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
    if i.period_start or i.period_end:
        entry["period"] = {
            k: v
            for k, v in {"start": fhir_instant(i.period_start), "end": fhir_instant(i.period_end)}.items()
            if v
        }
    assigner = _fhir_reference_with_identifier_fallback(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_questionnaire_contact(c: QuestionnaireContact) -> dict:
    entry: dict = {}
    if c.name:
        entry["name"] = c.name
    telecoms = [fhir_telecom(t) for t in (c.telecoms or [])]
    if telecoms:
        entry["telecom"] = telecoms
    return entry


def fhir_questionnaire_jurisdiction(j: QuestionnaireJurisdiction) -> dict:
    entry: dict = {}
    coding = _fhir_coding_list(j.codings)
    if coding:
        entry["coding"] = coding
    if j.text:
        entry["text"] = j.text
    return entry


def fhir_questionnaire_use_context(uc: QuestionnaireUseContext) -> dict:
    entry: dict = {
        "code": {
            k: v
            for k, v in {
                "system": uc.system,
                "version": uc.version,
                "code": uc.code,
                "display": uc.display,
                "userSelected": uc.user_selected,
            }.items()
            if v is not None
        }
    }

    if uc.value_codeable_concept_text or uc.value_codeable_concept_codings:
        cc: dict = {}
        coding = _fhir_coding_list(uc.value_codeable_concept_codings)
        if coding:
            cc["coding"] = coding
        if uc.value_codeable_concept_text:
            cc["text"] = uc.value_codeable_concept_text
        entry["valueCodeableConcept"] = cc
    elif uc.value_quantity_value is not None or uc.value_quantity_unit or uc.value_quantity_system or uc.value_quantity_code:
        entry["valueQuantity"] = _fhir_quantity(uc, "value_quantity")
    elif any([uc.value_range_low_value is not None, uc.value_range_high_value is not None]):
        rng: dict = {}
        low = _fhir_quantity(uc, "value_range_low")
        high = _fhir_quantity(uc, "value_range_high")
        if low:
            rng["low"] = low
        if high:
            rng["high"] = high
        entry["valueRange"] = rng
    elif uc.value_reference_reference or (uc.value_reference_type and uc.value_reference_id):
        ref = _fhir_reference(uc, "value_reference")
        if ref:
            entry["valueReference"] = ref

    return entry


def fhir_questionnaire_item_enable_when(ew: QuestionnaireItemEnableWhen) -> dict:
    entry: dict = {
        "question": ew.question,
        "operator": _OPERATOR_SYMBOLS.get(fhir_enum(ew.operator), fhir_enum(ew.operator)),
    }

    if ew.answer_boolean is not None:
        entry["answerBoolean"] = ew.answer_boolean
    elif ew.answer_decimal is not None:
        entry["answerDecimal"] = float(ew.answer_decimal)
    elif ew.answer_integer is not None:
        entry["answerInteger"] = ew.answer_integer
    elif ew.answer_date is not None:
        entry["answerDate"] = ew.answer_date.isoformat()
    elif ew.answer_date_time is not None:
        entry["answerDateTime"] = fhir_instant(ew.answer_date_time)
    elif ew.answer_time is not None:
        entry["answerTime"] = ew.answer_time.isoformat()
    elif ew.answer_string is not None:
        entry["answerString"] = ew.answer_string
    elif ew.system or ew.code:
        # FhirCodingMixin's bare attribute names — _coding_prefix
        # ("answer_coding_") only renames the DB column, never the Python
        # attribute (see CLAUDE.md's FhirCodingMixin invariant).
        entry["answerCoding"] = {
            k: v
            for k, v in {
                "system": ew.system,
                "version": ew.version,
                "code": ew.code,
                "display": ew.display,
                "userSelected": ew.user_selected,
            }.items()
            if v is not None
        }
    elif ew.answer_quantity_value is not None or ew.answer_quantity_unit or ew.answer_quantity_system or ew.answer_quantity_code:
        entry["answerQuantity"] = _fhir_quantity(ew, "answer_quantity")
    elif ew.answer_reference_reference or (ew.answer_reference_type and ew.answer_reference_id):
        ref = _fhir_reference(ew, "answer_reference")
        if ref:
            entry["answerReference"] = ref

    return entry


def fhir_questionnaire_item_answer_option(ao: QuestionnaireItemAnswerOption) -> dict:
    entry: dict = {}

    if ao.value_integer is not None:
        entry["valueInteger"] = ao.value_integer
    elif ao.value_date is not None:
        entry["valueDate"] = ao.value_date.isoformat()
    elif ao.value_time is not None:
        entry["valueTime"] = ao.value_time.isoformat()
    elif ao.value_string is not None:
        entry["valueString"] = ao.value_string
    elif ao.system or ao.code:
        entry["valueCoding"] = {
            k: v
            for k, v in {
                "system": ao.system,
                "version": ao.version,
                "code": ao.code,
                "display": ao.display,
                "userSelected": ao.user_selected,
            }.items()
            if v is not None
        }
    elif ao.value_reference_reference or (ao.value_reference_type and ao.value_reference_id):
        ref = _fhir_reference(ao, "value_reference")
        if ref:
            entry["valueReference"] = ref

    if ao.initial_selected is not None:
        entry["initialSelected"] = ao.initial_selected

    return entry


def fhir_questionnaire_item_initial(ini: QuestionnaireItemInitial) -> dict:
    entry: dict = {}

    if ini.value_boolean is not None:
        entry["valueBoolean"] = ini.value_boolean
    elif ini.value_decimal is not None:
        entry["valueDecimal"] = float(ini.value_decimal)
    elif ini.value_integer is not None:
        entry["valueInteger"] = ini.value_integer
    elif ini.value_date is not None:
        entry["valueDate"] = ini.value_date.isoformat()
    elif ini.value_date_time is not None:
        entry["valueDateTime"] = fhir_instant(ini.value_date_time)
    elif ini.value_time is not None:
        entry["valueTime"] = ini.value_time.isoformat()
    elif ini.value_string is not None:
        entry["valueString"] = ini.value_string
    elif ini.value_uri is not None:
        entry["valueUri"] = ini.value_uri
    elif ini.content_type or ini.url or ini.data or ini.title:
        # FhirAttachmentMixin's bare attribute names — _attachment_prefix
        # ("value_attachment_") only renames the DB column.
        entry["valueAttachment"] = {
            k: v
            for k, v in {
                "contentType": ini.content_type,
                "language": ini.language,
                "data": ini.data,
                "url": ini.url,
                "size": ini.size,
                "hash": ini.hash,
                "title": ini.title,
                "creation": fhir_instant(ini.creation),
            }.items()
            if v is not None
        }
    elif ini.system or ini.code:
        # FhirCodingMixin's bare attribute names.
        entry["valueCoding"] = {
            k: v
            for k, v in {
                "system": ini.system,
                "version": ini.version,
                "code": ini.code,
                "display": ini.display,
                "userSelected": ini.user_selected,
            }.items()
            if v is not None
        }
    elif ini.value_quantity_value is not None or ini.value_quantity_unit or ini.value_quantity_system or ini.value_quantity_code:
        entry["valueQuantity"] = _fhir_quantity(ini, "value_quantity")
    elif ini.value_reference_reference or (ini.value_reference_type and ini.value_reference_id):
        ref = _fhir_reference(ini, "value_reference")
        if ref:
            entry["valueReference"] = ref

    return entry


def _build_fhir_item_tree(items: list[QuestionnaireItem]) -> list[dict]:
    """Reconstructs the nested FHIR `item[]` shape from the flat, eager-
    loaded `QuestionnaireModel.items` collection (every item at every
    depth, see QuestionnaireModel's own docstring) by grouping on
    `parent_item_id` — O(n), no recursive queries."""
    by_parent: dict[int | None, list[QuestionnaireItem]] = {}
    for item in items:
        by_parent.setdefault(item.parent_item_id, []).append(item)

    def render(parent_id: int | None) -> list[dict]:
        result = []
        for item in by_parent.get(parent_id, []):
            entry: dict = {
                "linkId": item.link_id,
                "type": fhir_enum(item.type).replace("open_choice", "open-choice"),
            }
            if item.definition:
                entry["definition"] = item.definition
            coding = _fhir_coding_list(item.codings)
            if coding:
                entry["code"] = coding
            if item.prefix:
                entry["prefix"] = item.prefix
            if item.text:
                entry["text"] = item.text
            enable_whens = [fhir_questionnaire_item_enable_when(ew) for ew in (item.enable_whens or [])]
            if enable_whens:
                entry["enableWhen"] = enable_whens
            if item.enable_behavior:
                entry["enableBehavior"] = fhir_enum(item.enable_behavior)
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
            answer_options = [fhir_questionnaire_item_answer_option(ao) for ao in (item.answer_options or [])]
            if answer_options:
                entry["answerOption"] = answer_options
            initials = [fhir_questionnaire_item_initial(ini) for ini in (item.initials or [])]
            if initials:
                entry["initial"] = initials

            children = render(item.id)
            if children:
                entry["item"] = children

            result.append(entry)
        return result

    return render(None)


# Base URL for this server's own, not-yet-formally-registered extensions —
# same convention as every other resource's _fhir_meta.
_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(q: QuestionnaireModel) -> dict:
    """TenantAuditMixin's columns rendered into Resource.meta — mirrors
    app.fhir.mappers.organization.fhir._fhir_meta."""
    meta: dict = {}
    if q.updated_at:
        meta["lastUpdated"] = fhir_instant(q.updated_at)

    extensions = []
    if q.tenant_id:
        extensions.append({"url": f"{_EXT_BASE}/org-id", "valueString": q.tenant_id})
    if q.created_by:
        extensions.append({"url": f"{_EXT_BASE}/created-by", "valueString": q.created_by})
    if q.updated_by:
        extensions.append({"url": f"{_EXT_BASE}/updated-by", "valueString": q.updated_by})
    if q.created_at:
        extensions.append(
            {"url": f"{_EXT_BASE}/created-at", "valueDateTime": fhir_instant(q.created_at)}
        )
    if extensions:
        meta["extension"] = extensions

    return meta


def to_fhir_questionnaire(q: QuestionnaireModel) -> dict:
    result: dict = {
        "resourceType": "Questionnaire",
        "id": str(q.questionnaire_id),
    }

    meta = _fhir_meta(q)
    if meta:
        result["meta"] = meta

    if q.extension:
        result["extension"] = list(q.extension)

    if q.url:
        result["url"] = q.url

    identifiers = [fhir_questionnaire_identifier(i) for i in (q.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    if q.version:
        result["version"] = q.version
    if q.name:
        result["name"] = q.name
    if q.title:
        result["title"] = q.title
    if q.derived_from:
        result["derivedFrom"] = list(q.derived_from)
    if q.status:
        result["status"] = fhir_enum(q.status)
    if q.experimental is not None:
        result["experimental"] = q.experimental
    if q.subject_type:
        result["subjectType"] = list(q.subject_type)
    if q.date:
        result["date"] = fhir_instant(q.date)
    if q.publisher:
        result["publisher"] = q.publisher
    if q.description:
        result["description"] = q.description
    if q.purpose:
        result["purpose"] = q.purpose
    if q.copyright:
        result["copyright"] = q.copyright
    if q.approval_date:
        result["approvalDate"] = q.approval_date.isoformat()
    if q.last_review_date:
        result["lastReviewDate"] = q.last_review_date.isoformat()
    if q.effective_period_start or q.effective_period_end:
        result["effectivePeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(q.effective_period_start),
                "end": fhir_instant(q.effective_period_end),
            }.items()
            if v
        }

    coding = _fhir_coding_list(q.codings)
    if coding:
        result["code"] = coding

    contacts = [fhir_questionnaire_contact(c) for c in (q.contacts or [])]
    if contacts:
        result["contact"] = contacts

    use_contexts = [fhir_questionnaire_use_context(uc) for uc in (q.use_contexts or [])]
    if use_contexts:
        result["useContext"] = use_contexts

    jurisdictions = [fhir_questionnaire_jurisdiction(j) for j in (q.jurisdictions or [])]
    if jurisdictions:
        result["jurisdiction"] = jurisdictions

    items = _build_fhir_item_tree(q.items or [])
    if items:
        result["item"] = items

    return {k: v for k, v in result.items() if v is not None}
