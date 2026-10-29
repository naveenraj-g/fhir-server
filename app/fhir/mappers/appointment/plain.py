from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.appointment import AppointmentModel


def _audit_fields(obj) -> dict:
    """created_at/updated_at/created_by/updated_by — every Appointment
    sub-resource row carries these."""
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def plain_coding(c) -> dict:
    """One Coding entry (FhirCodingMixin-shaped row) → plain dict —
    mirrors app.fhir.mappers.slot.plain.plain_coding."""
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
    app.fhir.mappers.slot.plain._plain_reference_fields."""
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


def plain_appointment_identifier(i) -> dict:
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


def _plain_cc_row(obj) -> dict:
    return {
        "id": obj.id,
        "codings": [plain_coding(x) for x in (obj.codings or [])],
        "text": obj.text,
        **_audit_fields(obj),
    }


def plain_appointment_service_category(sc) -> dict:
    return _plain_cc_row(sc)


def plain_appointment_service_type(st) -> dict:
    return _plain_cc_row(st)


def plain_appointment_specialty(sp) -> dict:
    return _plain_cc_row(sp)


def plain_appointment_reason_code(rc) -> dict:
    return _plain_cc_row(rc)


def _plain_reference_row(obj) -> dict:
    return {
        "id": obj.id,
        **_plain_reference_fields(obj, "reference"),
        **_audit_fields(obj),
    }


def plain_appointment_reason_reference(rr) -> dict:
    return _plain_reference_row(rr)


def plain_appointment_supporting_information(si) -> dict:
    return _plain_reference_row(si)


def plain_appointment_slot(s) -> dict:
    return _plain_reference_row(s)


def plain_appointment_based_on(bo) -> dict:
    return _plain_reference_row(bo)


def plain_appointment_requested_period(rp) -> dict:
    return {
        "id": rp.id,
        "start": rp.start.isoformat() if rp.start else None,
        "end": rp.end.isoformat() if rp.end else None,
        **_audit_fields(rp),
    }


def plain_appointment_participant_type(pt) -> dict:
    return {
        "id": pt.id,
        "codings": [plain_coding(c) for c in (pt.codings or [])],
        "text": pt.text,
        **_audit_fields(pt),
    }


def plain_appointment_participant(p) -> dict:
    return {
        "id": p.id,
        "types": [plain_appointment_participant_type(t) for t in (p.types or [])],
        **_plain_reference_fields(p, "actor"),
        "required": fhir_enum(p.required),
        "status": fhir_enum(p.status),
        "period_start": p.period_start.isoformat() if p.period_start else None,
        "period_end": p.period_end.isoformat() if p.period_end else None,
        **_audit_fields(p),
    }


def to_plain_appointment(appointment: AppointmentModel) -> dict:
    return {
        "id": appointment.appointment_id,
        "extension": appointment.extension or [],
        "status": fhir_enum(appointment.status),
        "cancelation_reason_codings": [
            plain_coding(c) for c in (appointment.cancelation_reason_codings or [])
        ],
        "cancelation_reason_text": appointment.cancelation_reason_text,
        "appointment_type_codings": [
            plain_coding(c) for c in (appointment.appointment_type_codings or [])
        ],
        "appointment_type_text": appointment.appointment_type_text,
        "priority": appointment.priority,
        "description": appointment.description,
        "start": appointment.start.isoformat() if appointment.start else None,
        "end": appointment.end.isoformat() if appointment.end else None,
        "minutes_duration": appointment.minutes_duration,
        "created": appointment.created.isoformat() if appointment.created else None,
        "comment": appointment.comment,
        "patient_instruction": appointment.patient_instruction,
        "identifier": [plain_appointment_identifier(i) for i in (appointment.identifiers or [])],
        "service_category": [
            plain_appointment_service_category(sc) for sc in (appointment.service_categories or [])
        ],
        "service_type": [
            plain_appointment_service_type(st) for st in (appointment.service_types or [])
        ],
        "specialty": [plain_appointment_specialty(sp) for sp in (appointment.specialties or [])],
        "reason_code": [plain_appointment_reason_code(rc) for rc in (appointment.reason_codes or [])],
        "reason_reference": [
            plain_appointment_reason_reference(rr) for rr in (appointment.reason_references or [])
        ],
        "supporting_information": [
            plain_appointment_supporting_information(si)
            for si in (appointment.supporting_informations or [])
        ],
        "slot": [plain_appointment_slot(s) for s in (appointment.slots or [])],
        "based_on": [plain_appointment_based_on(bo) for bo in (appointment.based_ons or [])],
        "requested_period": [
            plain_appointment_requested_period(rp) for rp in (appointment.requested_periods or [])
        ],
        "participant": [plain_appointment_participant(p) for p in (appointment.participants or [])],
        "org_id": appointment.tenant_id,
        "created_at": appointment.created_at.isoformat() if appointment.created_at else None,
        "updated_at": appointment.updated_at.isoformat() if appointment.updated_at else None,
        "created_by": appointment.created_by,
        "updated_by": appointment.updated_by,
    }
