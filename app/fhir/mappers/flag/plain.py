from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.flag import (
        FlagCategory,
        FlagIdentifier,
        FlagModel,
    )


def _plain_coding(c) -> dict:
    return {
        "id": c.id,
        "system": c.system,
        "version": c.version,
        "code": c.code,
        "display": c.display,
        "user_selected": c.user_selected,
        "tenant_id": c.tenant_id,
        "created_by": c.created_by,
        "updated_by": c.updated_by,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


def _plain_identifier(i: FlagIdentifier) -> dict:
    return {
        "id": i.id,
        "use": fhir_enum(i.use),
        "type_text": i.type_text,
        "type_codings": [_plain_coding(c) for c in (i.type_codings or [])],
        "system": i.system,
        "value": i.value,
        "period_start": fhir_instant(i.period_start),
        "period_end": fhir_instant(i.period_end),
        "assigner_reference": i.assigner_reference,
        "assigner": (
            f"Organization/{i.assigner_id}"
            if (i.assigner_id and fhir_enum(i.assigner_type) == "Organization")
            else i.assigner_reference
        ),
        "assigner_type": fhir_enum(i.assigner_type),
        "assigner_id": i.assigner_id,
        "assigner_display": i.assigner_display,
        "assigner_identifier_use": fhir_enum(i.assigner_identifier_use),
        "assigner_identifier_type_system": i.assigner_identifier_type_system,
        "assigner_identifier_type_version": i.assigner_identifier_type_version,
        "assigner_identifier_type_code": i.assigner_identifier_type_code,
        "assigner_identifier_type_display": i.assigner_identifier_type_display,
        "assigner_identifier_type_text": i.assigner_identifier_type_text,
        "assigner_identifier_type_user_selected": i.assigner_identifier_type_user_selected,
        "assigner_identifier_system": i.assigner_identifier_system,
        "assigner_identifier_value": i.assigner_identifier_value,
        "assigner_identifier_period_start": fhir_instant(
            i.assigner_identifier_period_start
        ),
        "assigner_identifier_period_end": fhir_instant(
            i.assigner_identifier_period_end
        ),
        "tenant_id": i.tenant_id,
        "created_by": i.created_by,
        "updated_by": i.updated_by,
        "created_at": i.created_at,
        "updated_at": i.updated_at,
    }


def _plain_category(cat: FlagCategory) -> dict:
    return {
        "id": cat.id,
        "text": cat.text,
        "codings": [_plain_coding(c) for c in (cat.codings or [])],
        "tenant_id": cat.tenant_id,
        "created_by": cat.created_by,
        "updated_by": cat.updated_by,
        "created_at": cat.created_at,
        "updated_at": cat.updated_at,
    }


def to_plain_flag(model: FlagModel) -> dict:
    """Serialize a FlagModel to plain snake_case dict."""
    return {
        "id": model.flag_id,
        "status": fhir_enum(model.status),
        "code_text": model.code_text,
        "code_codings": [_plain_coding(c) for c in (model.code_codings or [])],
        "subject_reference": model.subject_reference,
        "subject_type": fhir_enum(model.subject_type),
        "subject_id": model.subject_id,
        "subject_display": model.subject_display,
        "period_start": fhir_instant(model.period_start),
        "period_end": fhir_instant(model.period_end),
        "encounter_reference": model.encounter_reference,
        "encounter_type": fhir_enum(model.encounter_type),
        "encounter_id": model.encounter_id,
        "encounter_display": model.encounter_display,
        "author_reference": model.author_reference,
        "author_type": fhir_enum(model.author_type),
        "author_id": model.author_id,
        "author_display": model.author_display,
        "extension": list(model.extension) if model.extension else [],
        "tenant_id": model.tenant_id,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
        "identifiers": [_plain_identifier(i) for i in (model.identifiers or [])],
        "categories": [_plain_category(c) for c in (model.categories or [])],
    }
