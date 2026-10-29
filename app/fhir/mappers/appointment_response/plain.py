from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.appointment_response import AppointmentResponseModel


def _audit_fields(obj) -> dict:
    """created_at/updated_at/created_by/updated_by — every
    AppointmentResponse sub-resource row carries these."""
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def plain_coding(c) -> dict:
    """One Coding entry (FhirCodingMixin-shaped row) → plain dict —
    mirrors app.fhir.mappers.appointment.plain.plain_coding."""
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
    """Flat `{prefix}_type`/`{prefix}_id`/`{prefix}_display` + `{prefix}_identifier_*`
    fallback fields for a resolved-or-logical Reference, plus a resolved
    `{prefix}` FHIR-reference-string convenience field — mirrors
    app.fhir.mappers.appointment.plain._plain_reference_fields."""
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    return {
        prefix: f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None,
        f"{prefix}_type": fhir_enum(ref_type),
        f"{prefix}_id": ref_id,
        f"{prefix}_display": getattr(obj, f"{prefix}_display", None),
        f"{prefix}_identifier_use": fhir_enum(getattr(obj, f"{prefix}_identifier_use", None)),
        f"{prefix}_identifier_type_system": getattr(obj, f"{prefix}_identifier_type_system", None),
        f"{prefix}_identifier_type_version": getattr(obj, f"{prefix}_identifier_type_version", None),
        f"{prefix}_identifier_type_code": getattr(obj, f"{prefix}_identifier_type_code", None),
        f"{prefix}_identifier_type_display": getattr(obj, f"{prefix}_identifier_type_display", None),
        f"{prefix}_identifier_type_text": getattr(obj, f"{prefix}_identifier_type_text", None),
        f"{prefix}_identifier_type_user_selected": getattr(
            obj, f"{prefix}_identifier_type_user_selected", None
        ),
        f"{prefix}_identifier_system": getattr(obj, f"{prefix}_identifier_system", None),
        f"{prefix}_identifier_value": getattr(obj, f"{prefix}_identifier_value", None),
        f"{prefix}_identifier_period_start": id_period_start.isoformat() if id_period_start else None,
        f"{prefix}_identifier_period_end": id_period_end.isoformat() if id_period_end else None,
    }


def plain_appointment_response_identifier(i) -> dict:
    return {
        "id": i.id,
        "use": fhir_enum(i.use),
        "type_codings": [plain_coding(c) for c in (i.type_codings or [])],
        "type_text": i.type_text,
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start.isoformat() if i.period_start else None,
        "period_end": i.period_end.isoformat() if i.period_end else None,
        **_plain_reference_fields(i, "assigner"),
        **_audit_fields(i),
    }


def plain_appointment_response_participant_type(pt) -> dict:
    return {
        "id": pt.id,
        "codings": [plain_coding(c) for c in (pt.codings or [])],
        "text": pt.text,
        **_audit_fields(pt),
    }


def to_plain_appointment_response(appointment_response: AppointmentResponseModel) -> dict:
    return {
        "id": appointment_response.appointment_response_id,
        "extension": appointment_response.extension or [],
        **_plain_reference_fields(appointment_response, "appointment"),
        "start": appointment_response.start.isoformat() if appointment_response.start else None,
        "end": appointment_response.end.isoformat() if appointment_response.end else None,
        **_plain_reference_fields(appointment_response, "actor"),
        "participant_status": fhir_enum(appointment_response.participant_status),
        "comment": appointment_response.comment,
        "identifier": [
            plain_appointment_response_identifier(i)
            for i in (appointment_response.identifiers or [])
        ],
        "participant_type": [
            plain_appointment_response_participant_type(pt)
            for pt in (appointment_response.participant_types or [])
        ],
        "org_id": appointment_response.tenant_id,
        "created_at": appointment_response.created_at.isoformat() if appointment_response.created_at else None,
        "updated_at": appointment_response.updated_at.isoformat() if appointment_response.updated_at else None,
        "created_by": appointment_response.created_by,
        "updated_by": appointment_response.updated_by,
    }
