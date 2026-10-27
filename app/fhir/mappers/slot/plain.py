from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.slot import SlotModel


def _audit_fields(obj) -> dict:
    """created_at/updated_at/created_by/updated_by — every Slot
    sub-resource row carries these."""
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def plain_coding(c) -> dict:
    """One Coding entry (FhirCodingMixin-shaped row) → plain dict. Shared by
    every Slot CodeableConcept field's coding[] — mirrors
    app.fhir.mappers.schedule.plain.plain_coding."""
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
    `{prefix}` FHIR-reference-string convenience field. Shared by every
    flattened Reference field on Slot (identifier.assigner, schedule) —
    mirrors app.fhir.mappers.schedule.plain._plain_reference_fields."""
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
    """Slot.identifier (Identifier) → plain snake_case dict. `type_codings`
    is a real 0..* child table rather than a single flattened coding —
    mirrors app.fhir.mappers.schedule.plain.plain_sch_identifier."""
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


def plain_slot_service_category(sc) -> dict:
    return {
        "id": sc.id,
        "codings": [plain_coding(x) for x in (sc.codings or [])],
        "text": sc.text,
        **_audit_fields(sc),
    }


def plain_slot_service_type(st) -> dict:
    return {
        "id": st.id,
        "codings": [plain_coding(x) for x in (st.codings or [])],
        "text": st.text,
        **_audit_fields(st),
    }


def plain_slot_specialty(sp) -> dict:
    return {
        "id": sp.id,
        "codings": [plain_coding(x) for x in (sp.codings or [])],
        "text": sp.text,
        **_audit_fields(sp),
    }


def to_plain_slot(slot: SlotModel) -> dict:
    return {
        "id": slot.slot_id,
        "extension": slot.extension or [],
        **_plain_reference_fields(slot, "schedule"),
        "status": fhir_enum(slot.status),
        "start": slot.start.isoformat() if slot.start else None,
        "end": slot.end.isoformat() if slot.end else None,
        "appointment_type_codings": [
            plain_coding(c) for c in (slot.appointment_type_codings or [])
        ],
        "appointment_type_text": slot.appointment_type_text,
        "overbooked": slot.overbooked,
        "comment": slot.comment,
        "identifier": [plain_slot_identifier(i) for i in (slot.identifiers or [])],
        "service_category": [
            plain_slot_service_category(sc) for sc in (slot.service_categories or [])
        ],
        "service_type": [
            plain_slot_service_type(st) for st in (slot.service_types or [])
        ],
        "specialty": [plain_slot_specialty(sp) for sp in (slot.specialties or [])],
        "org_id": slot.tenant_id,
        "created_at": slot.created_at.isoformat() if slot.created_at else None,
        "updated_at": slot.updated_at.isoformat() if slot.updated_at else None,
        "created_by": slot.created_by,
        "updated_by": slot.updated_by,
    }
