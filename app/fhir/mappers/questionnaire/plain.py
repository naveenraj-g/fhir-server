from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

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


def _audit_fields(obj) -> dict:
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def plain_coding(c) -> dict:
    return {
        "id": c.id,
        "system": c.system,
        "version": c.version,
        "code": c.code,
        "display": c.display,
        "user_selected": c.user_selected,
        **_audit_fields(c),
    }


def _plain_reference_fields(obj, prefix: str) -> dict:
    """Mirrors app.fhir.mappers.organization.plain._plain_reference_fields —
    raw `{prefix}_reference` + resolved type/id/display + a convenience
    `{prefix}` resolved-reference-string field."""
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    return {
        f"{prefix}_reference": getattr(obj, f"{prefix}_reference", None),
        prefix: f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None,
        f"{prefix}_type": fhir_enum(ref_type),
        f"{prefix}_id": ref_id,
        f"{prefix}_display": getattr(obj, f"{prefix}_display", None),
    }


def _plain_reference_with_identifier_fallback(obj, prefix: str) -> dict:
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)
    return {
        **_plain_reference_fields(obj, prefix),
        f"{prefix}_identifier_use": fhir_enum(getattr(obj, f"{prefix}_identifier_use", None)),
        f"{prefix}_identifier_type_system": getattr(obj, f"{prefix}_identifier_type_system", None),
        f"{prefix}_identifier_type_version": getattr(obj, f"{prefix}_identifier_type_version", None),
        f"{prefix}_identifier_type_code": getattr(obj, f"{prefix}_identifier_type_code", None),
        f"{prefix}_identifier_type_display": getattr(obj, f"{prefix}_identifier_type_display", None),
        f"{prefix}_identifier_type_text": getattr(obj, f"{prefix}_identifier_type_text", None),
        f"{prefix}_identifier_type_user_selected": getattr(obj, f"{prefix}_identifier_type_user_selected", None),
        f"{prefix}_identifier_system": getattr(obj, f"{prefix}_identifier_system", None),
        f"{prefix}_identifier_value": getattr(obj, f"{prefix}_identifier_value", None),
        f"{prefix}_identifier_period_start": id_period_start.isoformat() if id_period_start else None,
        f"{prefix}_identifier_period_end": id_period_end.isoformat() if id_period_end else None,
    }


def plain_questionnaire_identifier(i: QuestionnaireIdentifier) -> dict:
    return {
        "id": i.id,
        "use": fhir_enum(i.use),
        "type_codings": [plain_coding(c) for c in (i.type_codings or [])],
        "type_text": i.type_text,
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start.isoformat() if i.period_start else None,
        "period_end": i.period_end.isoformat() if i.period_end else None,
        **_plain_reference_with_identifier_fallback(i, "assigner"),
        **_audit_fields(i),
    }


def plain_questionnaire_contact(c: QuestionnaireContact) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "telecoms": [
            {
                "id": t.id,
                "system": fhir_enum(t.system),
                "value": t.value,
                "use": fhir_enum(t.use),
                "rank": t.rank,
                "period_start": t.period_start.isoformat() if t.period_start else None,
                "period_end": t.period_end.isoformat() if t.period_end else None,
                **_audit_fields(t),
            }
            for t in (c.telecoms or [])
        ],
        **_audit_fields(c),
    }


def plain_questionnaire_jurisdiction(j: QuestionnaireJurisdiction) -> dict:
    return {
        "id": j.id,
        "codings": [plain_coding(c) for c in (j.codings or [])],
        "text": j.text,
        **_audit_fields(j),
    }


def plain_questionnaire_use_context(uc: QuestionnaireUseContext) -> dict:
    return {
        "id": uc.id,
        "code_system": uc.system,
        "code_version": uc.version,
        "code_code": uc.code,
        "code_display": uc.display,
        "code_user_selected": uc.user_selected,
        "value_codeable_concept_codings": [plain_coding(c) for c in (uc.value_codeable_concept_codings or [])],
        "value_codeable_concept_text": uc.value_codeable_concept_text,
        "value_quantity_value": float(uc.value_quantity_value) if uc.value_quantity_value is not None else None,
        "value_quantity_comparator": fhir_enum(uc.value_quantity_comparator),
        "value_quantity_unit": uc.value_quantity_unit,
        "value_quantity_system": uc.value_quantity_system,
        "value_quantity_code": uc.value_quantity_code,
        "value_range_low_value": float(uc.value_range_low_value) if uc.value_range_low_value is not None else None,
        "value_range_low_unit": uc.value_range_low_unit,
        "value_range_low_system": uc.value_range_low_system,
        "value_range_low_code": uc.value_range_low_code,
        "value_range_high_value": float(uc.value_range_high_value) if uc.value_range_high_value is not None else None,
        "value_range_high_unit": uc.value_range_high_unit,
        "value_range_high_system": uc.value_range_high_system,
        "value_range_high_code": uc.value_range_high_code,
        **_plain_reference_fields(uc, "value_reference"),
        **_audit_fields(uc),
    }


def plain_questionnaire_item_enable_when(ew: QuestionnaireItemEnableWhen) -> dict:
    return {
        "id": ew.id,
        "question": ew.question,
        "operator": fhir_enum(ew.operator),
        "answer_boolean": ew.answer_boolean,
        "answer_decimal": float(ew.answer_decimal) if ew.answer_decimal is not None else None,
        "answer_integer": ew.answer_integer,
        "answer_date": ew.answer_date.isoformat() if ew.answer_date else None,
        "answer_date_time": ew.answer_date_time.isoformat() if ew.answer_date_time else None,
        "answer_time": ew.answer_time.isoformat() if ew.answer_time else None,
        "answer_string": ew.answer_string,
        # FhirCodingMixin's bare attribute names.
        "answer_coding_system": ew.system,
        "answer_coding_version": ew.version,
        "answer_coding_code": ew.code,
        "answer_coding_display": ew.display,
        "answer_coding_user_selected": ew.user_selected,
        "answer_quantity_value": float(ew.answer_quantity_value) if ew.answer_quantity_value is not None else None,
        "answer_quantity_comparator": fhir_enum(ew.answer_quantity_comparator),
        "answer_quantity_unit": ew.answer_quantity_unit,
        "answer_quantity_system": ew.answer_quantity_system,
        "answer_quantity_code": ew.answer_quantity_code,
        **_plain_reference_fields(ew, "answer_reference"),
        **_audit_fields(ew),
    }


def plain_questionnaire_item_answer_option(ao: QuestionnaireItemAnswerOption) -> dict:
    return {
        "id": ao.id,
        "value_integer": ao.value_integer,
        "value_date": ao.value_date.isoformat() if ao.value_date else None,
        "value_time": ao.value_time.isoformat() if ao.value_time else None,
        "value_string": ao.value_string,
        # FhirCodingMixin's bare attribute names.
        "value_coding_system": ao.system,
        "value_coding_version": ao.version,
        "value_coding_code": ao.code,
        "value_coding_display": ao.display,
        "value_coding_user_selected": ao.user_selected,
        "initial_selected": ao.initial_selected,
        **_plain_reference_fields(ao, "value_reference"),
        **_audit_fields(ao),
    }


def plain_questionnaire_item_initial(ini: QuestionnaireItemInitial) -> dict:
    return {
        "id": ini.id,
        "value_boolean": ini.value_boolean,
        "value_decimal": float(ini.value_decimal) if ini.value_decimal is not None else None,
        "value_integer": ini.value_integer,
        "value_date": ini.value_date.isoformat() if ini.value_date else None,
        "value_date_time": ini.value_date_time.isoformat() if ini.value_date_time else None,
        "value_time": ini.value_time.isoformat() if ini.value_time else None,
        "value_string": ini.value_string,
        "value_uri": ini.value_uri,
        # FhirAttachmentMixin/FhirCodingMixin bare attribute names below —
        # _attachment_prefix/_coding_prefix only rename the DB column.
        "value_attachment": {
            "id": ini.id,
            "content_type": ini.content_type,
            "language": ini.language,
            "data": ini.data,
            "url": ini.url,
            "size": ini.size,
            "hash": ini.hash,
            "title": ini.title,
            "creation": ini.creation.isoformat() if ini.creation else None,
            **_audit_fields(ini),
        }
        if any([ini.content_type, ini.url, ini.data, ini.title])
        else None,
        "value_coding_system": ini.system,
        "value_coding_version": ini.version,
        "value_coding_code": ini.code,
        "value_coding_display": ini.display,
        "value_coding_user_selected": ini.user_selected,
        "value_quantity_value": float(ini.value_quantity_value) if ini.value_quantity_value is not None else None,
        "value_quantity_comparator": fhir_enum(ini.value_quantity_comparator),
        "value_quantity_unit": ini.value_quantity_unit,
        "value_quantity_system": ini.value_quantity_system,
        "value_quantity_code": ini.value_quantity_code,
        **_plain_reference_fields(ini, "value_reference"),
        **_audit_fields(ini),
    }


def _build_plain_item_tree(items: list[QuestionnaireItem]) -> list[dict]:
    """Plain-dict mirror of app.fhir.mappers.questionnaire.fhir._build_fhir_item_tree —
    same flat-list-grouped-by-parent_item_id reconstruction."""
    by_parent: dict[int | None, list[QuestionnaireItem]] = {}
    for item in items:
        by_parent.setdefault(item.parent_item_id, []).append(item)

    def render(parent_id: int | None) -> list[dict]:
        result = []
        for item in by_parent.get(parent_id, []):
            result.append(
                {
                    "id": item.id,
                    "link_id": item.link_id,
                    "definition": item.definition,
                    "codings": [plain_coding(c) for c in (item.codings or [])],
                    "prefix": item.prefix,
                    "text": item.text,
                    "type": fhir_enum(item.type),
                    "enable_whens": [plain_questionnaire_item_enable_when(ew) for ew in (item.enable_whens or [])],
                    "enable_behavior": fhir_enum(item.enable_behavior),
                    "required": item.required,
                    "repeats": item.repeats,
                    "read_only": item.read_only,
                    "max_length": item.max_length,
                    "answer_value_set": item.answer_value_set,
                    "answer_options": [plain_questionnaire_item_answer_option(ao) for ao in (item.answer_options or [])],
                    "initials": [plain_questionnaire_item_initial(ini) for ini in (item.initials or [])],
                    "item": render(item.id),
                    **_audit_fields(item),
                }
            )
        return result

    return render(None)


def to_plain_questionnaire(q: QuestionnaireModel) -> dict:
    return {
        "id": q.questionnaire_id,
        "extension": q.extension or [],
        "url": q.url,
        "identifier": [plain_questionnaire_identifier(i) for i in (q.identifiers or [])],
        "version": q.version,
        "name": q.name,
        "title": q.title,
        "derived_from": list(q.derived_from) if q.derived_from else None,
        "status": fhir_enum(q.status),
        "experimental": q.experimental,
        "subject_type": list(q.subject_type) if q.subject_type else None,
        "date": q.date.isoformat() if q.date else None,
        "publisher": q.publisher,
        "description": q.description,
        "purpose": q.purpose,
        "copyright": q.copyright,
        "approval_date": q.approval_date.isoformat() if q.approval_date else None,
        "last_review_date": q.last_review_date.isoformat() if q.last_review_date else None,
        "effective_period_start": q.effective_period_start.isoformat() if q.effective_period_start else None,
        "effective_period_end": q.effective_period_end.isoformat() if q.effective_period_end else None,
        "codings": [plain_coding(c) for c in (q.codings or [])],
        "contact": [plain_questionnaire_contact(c) for c in (q.contacts or [])],
        "use_context": [plain_questionnaire_use_context(uc) for uc in (q.use_contexts or [])],
        "jurisdiction": [plain_questionnaire_jurisdiction(j) for j in (q.jurisdictions or [])],
        "item": _build_plain_item_tree(q.items or []),
        "user_id": q.user_id,
        "org_id": q.tenant_id,
        "created_at": q.created_at.isoformat() if q.created_at else None,
        "updated_at": q.updated_at.isoformat() if q.updated_at else None,
        "created_by": q.created_by,
        "updated_by": q.updated_by,
    }
