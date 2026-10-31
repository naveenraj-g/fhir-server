from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.document_reference import DocumentReferenceModel


def _plain_coding_list(codings) -> list[dict] | None:
    if not codings:
        return None
    return [
        {
            "id": getattr(c, "id", None),
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
        }
        for c in codings
    ]


def _plain_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _plain_coding_list(codings)
    if not coding_list and text is None:
        return None
    return {
        "text": text,
        "coding": coding_list,
    }


def _plain_ref(ref_raw: str | None, ref_type, ref_id: int | None, display: str | None) -> dict | None:
    if not (ref_raw or ref_type or ref_id or display):
        return None
    return {
        "reference": ref_raw or (f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None),
        "type": fhir_enum(ref_type) if ref_type else None,
        "id": ref_id,
        "display": display,
    }


def _plain_identifier(i) -> dict:
    return {
        "id": getattr(i, "id", None),
        "use": fhir_enum(i.use) if i.use else None,
        "type_text": i.type_text,
        "type_coding": _plain_coding_list(getattr(i, "type_codings", None)),
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start,
        "period_end": i.period_end,
        "assigner_reference": i.assigner_reference,
        "assigner_type": fhir_enum(i.assigner_type) if i.assigner_type else None,
        "assigner_id": i.assigner_id,
        "assigner_display": i.assigner_display,
        "assigner_identifier_use": fhir_enum(i.assigner_identifier_use) if i.assigner_identifier_use else None,
        "assigner_identifier_system": i.assigner_identifier_system,
        "assigner_identifier_value": i.assigner_identifier_value,
        "assigner_identifier_type_text": i.assigner_identifier_type_text,
    }


def _plain_master_identifier(model: DocumentReferenceModel) -> dict | None:
    has_any = (
        model.master_identifier_use
        or model.master_identifier_type_text
        or model.master_identifier_system
        or model.master_identifier_value
        or model.master_identifier_period_start
        or model.master_identifier_period_end
        or model.master_identifier_assigner_reference
        or model.master_identifier_assigner_type
        or model.master_identifier_assigner_id
        or getattr(model, "master_identifier_type_codings", None)
    )
    if not has_any:
        return None

    return {
        "use": fhir_enum(model.master_identifier_use) if model.master_identifier_use else None,
        "type_text": model.master_identifier_type_text,
        "type_coding": _plain_coding_list(getattr(model, "master_identifier_type_codings", None)),
        "system": model.master_identifier_system,
        "value": model.master_identifier_value,
        "period_start": model.master_identifier_period_start,
        "period_end": model.master_identifier_period_end,
        "assigner_reference": model.master_identifier_assigner_reference,
        "assigner_type": fhir_enum(model.master_identifier_assigner_type) if model.master_identifier_assigner_type else None,
        "assigner_id": model.master_identifier_assigner_id,
        "assigner_display": model.master_identifier_assigner_display,
        "assigner_identifier_use": fhir_enum(model.master_identifier_assigner_identifier_use) if model.master_identifier_assigner_identifier_use else None,
        "assigner_identifier_system": model.master_identifier_assigner_identifier_system,
        "assigner_identifier_value": model.master_identifier_assigner_identifier_value,
        "assigner_identifier_type_text": model.master_identifier_assigner_identifier_type_text,
    }


def _plain_content(c) -> dict:
    attachment = {
        "content_type": c.content_type,
        "language": c.language,
        "data": c.data,
        "url": c.url,
        "size": c.size,
        "hash": c.hash,
        "title": c.title,
        "creation": c.creation,
    }

    format_dict = None
    has_format = (
        c.format_system
        or c.format_version
        or c.format_code
        or c.format_display
        or c.format_user_selected is not None
    )
    if has_format:
        format_dict = {
            "system": c.format_system,
            "version": c.format_version,
            "code": c.format_code,
            "display": c.format_display,
            "user_selected": c.format_user_selected,
        }

    return {
        "id": getattr(c, "id", None),
        "attachment": attachment,
        "format": format_dict,
    }


def _plain_context(model: DocumentReferenceModel) -> dict | None:
    has_encounters = bool(getattr(model, "context_encounters", None))
    has_events = bool(getattr(model, "context_events", None))
    has_period = model.context_period_start or model.context_period_end
    has_facility = model.context_facility_type_text or bool(getattr(model, "context_facility_type_codings", None))
    has_practice = model.context_practice_setting_text or bool(getattr(model, "context_practice_setting_codings", None))
    has_patient_info = model.context_source_patient_info_reference or (
        model.context_source_patient_info_type and model.context_source_patient_info_id
    ) or model.context_source_patient_info_display
    has_related = bool(getattr(model, "context_related", None))

    if not (
        has_encounters
        or has_events
        or has_period
        or has_facility
        or has_practice
        or has_patient_info
        or has_related
    ):
        return None

    ctx: dict = {}
    if has_encounters:
        ctx["encounter"] = [
            _plain_ref(e.reference_reference, e.reference_type, e.reference_id, e.reference_display)
            for e in model.context_encounters
        ]

    if has_events:
        ctx["event"] = [
            _plain_codeable_concept(getattr(ev, "codings", None), ev.text)
            for ev in model.context_events
        ]

    if has_period:
        ctx["period_start"] = model.context_period_start
        ctx["period_end"] = model.context_period_end

    if has_facility:
        ctx["facility_type"] = _plain_codeable_concept(
            getattr(model, "context_facility_type_codings", None),
            model.context_facility_type_text,
        )

    if has_practice:
        ctx["practice_setting"] = _plain_codeable_concept(
            getattr(model, "context_practice_setting_codings", None),
            model.context_practice_setting_text,
        )

    if has_patient_info:
        ctx["source_patient_info"] = _plain_ref(
            model.context_source_patient_info_reference,
            model.context_source_patient_info_type,
            model.context_source_patient_info_id,
            model.context_source_patient_info_display,
        )

    if has_related:
        ctx["related"] = [
            _plain_ref(r.reference_reference, r.reference_type, r.reference_id, r.reference_display)
            for r in model.context_related
        ]

    return ctx


def to_plain_document_reference(model: DocumentReferenceModel) -> dict:
    """Map DocumentReferenceModel ORM instance to a plain snake_case dict."""
    return {
        "id": model.document_reference_id,
        "tenant_id": model.tenant_id,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
        "master_identifier": _plain_master_identifier(model),
        "identifier": [_plain_identifier(i) for i in getattr(model, "identifiers", [])] or None,
        "status": fhir_enum(model.status),
        "doc_status": fhir_enum(model.doc_status) if model.doc_status else None,
        "type": _plain_codeable_concept(getattr(model, "type_codings", None), model.type_text),
        "category": [
            _plain_codeable_concept(getattr(c, "codings", None), c.text)
            for c in getattr(model, "categories", [])
        ] or None,
        "subject": _plain_ref(
            model.subject_reference,
            model.subject_type,
            model.subject_id,
            model.subject_display,
        ),
        "date": model.date,
        "author": [
            _plain_ref(a.author_reference, a.author_type, a.author_id, a.author_display)
            for a in getattr(model, "authors", [])
        ] or None,
        "authenticator": _plain_ref(
            model.authenticator_reference,
            model.authenticator_type,
            model.authenticator_id,
            model.authenticator_display,
        ),
        "custodian": _plain_ref(
            model.custodian_reference,
            model.custodian_type,
            model.custodian_id,
            model.custodian_display,
        ),
        "relates_to": [
            {
                "id": getattr(r, "id", None),
                "code": fhir_enum(r.code),
                "target_reference": r.target_reference,
                "target_type": fhir_enum(r.target_type) if r.target_type else None,
                "target_id": r.target_id,
                "target_display": r.target_display,
            }
            for r in getattr(model, "relates_to", [])
        ] or None,
        "description": model.description,
        "security_label": [
            _plain_codeable_concept(getattr(s, "codings", None), s.text)
            for s in getattr(model, "security_labels", [])
        ] or None,
        "content": [_plain_content(c) for c in getattr(model, "contents", [])],
        "context": _plain_context(model),
    }
