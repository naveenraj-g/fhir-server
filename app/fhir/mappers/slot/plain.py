from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.slot import SlotModel


def _audit_fields(obj) -> dict:
    """created_at/updated_at/created_by/updated_by — every Slot sub-resource
    row carries these."""
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def _plain_reference_fields(obj, prefix: str) -> dict:
    """Flat `{prefix}_type`/`{prefix}_id`/`{prefix}_display` + `{prefix}_identifier_*`
    fallback fields for a resolved-or-logical Reference, plus a resolved
    `{prefix}` FHIR-reference-string convenience field. Mirrors
    app.fhir.mappers.schedule.plain._plain_reference_fields — shared by
    Slot.schedule and Slot.identifier.assigner."""
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    return {
        prefix: f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None,
        f"{prefix}_type": fhir_enum(ref_type),
        f"{prefix}_id": ref_id,
        f"{prefix}_display": getattr(obj, f"{prefix}_display", None),
        f"{prefix}_identifier_use": fhir_enum(
            getattr(obj, f"{prefix}_identifier_use", None)
        ),
        f"{prefix}_identifier_type_system": getattr(
            obj, f"{prefix}_identifier_type_system", None
        ),
        f"{prefix}_identifier_type_version": getattr(
            obj, f"{prefix}_identifier_type_version", None
        ),
        f"{prefix}_identifier_type_code": getattr(
            obj, f"{prefix}_identifier_type_code", None
        ),
        f"{prefix}_identifier_type_display": getattr(
            obj, f"{prefix}_identifier_type_display", None
        ),
        f"{prefix}_identifier_type_text": getattr(
            obj, f"{prefix}_identifier_type_text", None
        ),
        f"{prefix}_identifier_type_user_selected": getattr(
            obj, f"{prefix}_identifier_type_user_selected", None
        ),
        f"{prefix}_identifier_system": getattr(
            obj, f"{prefix}_identifier_system", None
        ),
        f"{prefix}_identifier_value": getattr(obj, f"{prefix}_identifier_value", None),
        f"{prefix}_identifier_period_start": id_period_start.isoformat()
        if id_period_start
        else None,
        f"{prefix}_identifier_period_end": id_period_end.isoformat()
        if id_period_end
        else None,
    }


def plain_slot_identifier(i) -> dict:
    """Slot.identifier (Identifier) → plain snake_case dict. Resource-
    specific because assigner is a resolved Reference(Organization) with an
    identifier fallback, and because the row carries an audit trail."""
    return {
        "id": i.id,
        "org_id": i.org_id,
        "use": fhir_enum(i.use),
        "type_system": i.type_system,
        "type_version": i.type_version,
        "type_code": i.type_code,
        "type_display": i.type_display,
        "type_text": i.type_text,
        "type_user_selected": i.type_user_selected,
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start.isoformat() if i.period_start else None,
        "period_end": i.period_end.isoformat() if i.period_end else None,
        **_plain_reference_fields(i, "assigner"),
        **_audit_fields(i),
    }


def plain_slot_service_category(sc) -> dict:
    return {
        "id": sc.id,
        "coding_system": sc.coding_system,
        "coding_version": sc.coding_version,
        "coding_code": sc.coding_code,
        "coding_display": sc.coding_display,
        "text": sc.text,
        "coding_user_selected": sc.coding_user_selected,
        **_audit_fields(sc),
    }


def plain_slot_service_type(st) -> dict:
    return {
        "id": st.id,
        "coding_system": st.coding_system,
        "coding_version": st.coding_version,
        "coding_code": st.coding_code,
        "coding_display": st.coding_display,
        "text": st.text,
        "coding_user_selected": st.coding_user_selected,
        **_audit_fields(st),
    }


def plain_slot_specialty(sp) -> dict:
    return {
        "id": sp.id,
        "coding_system": sp.coding_system,
        "coding_version": sp.coding_version,
        "coding_code": sp.coding_code,
        "coding_display": sp.coding_display,
        "text": sp.text,
        "coding_user_selected": sp.coding_user_selected,
        **_audit_fields(sp),
    }


def to_plain_slot(slot: SlotModel) -> dict:
    return {
        "id": slot.slot_id,
        **_plain_reference_fields(slot, "schedule"),
        "status": fhir_enum(slot.status),
        "start": slot.start.isoformat() if slot.start else None,
        "end": slot.end.isoformat() if slot.end else None,
        "overbooked": slot.overbooked,
        "comment": slot.comment,
        "appointment_type_system": slot.appointment_type_system,
        "appointment_type_version": slot.appointment_type_version,
        "appointment_type_code": slot.appointment_type_code,
        "appointment_type_display": slot.appointment_type_display,
        "appointment_type_text": slot.appointment_type_text,
        "appointment_type_user_selected": slot.appointment_type_user_selected,
        "identifier": [plain_slot_identifier(i) for i in (slot.identifiers or [])],
        "service_category": [
            plain_slot_service_category(sc) for sc in (slot.service_categories or [])
        ],
        "service_type": [
            plain_slot_service_type(st) for st in (slot.service_types or [])
        ],
        "specialty": [plain_slot_specialty(sp) for sp in (slot.specialties or [])],
        "org_id": slot.org_id,
        "created_at": slot.created_at.isoformat() if slot.created_at else None,
        "updated_at": slot.updated_at.isoformat() if slot.updated_at else None,
        "created_by": slot.created_by,
        "updated_by": slot.updated_by,
    }
