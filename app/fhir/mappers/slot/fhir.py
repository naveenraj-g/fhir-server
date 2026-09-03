from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.slot import SlotModel


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback for when the target isn't a resource in this system. Mirrors
    app.fhir.mappers.schedule.fhir._fhir_reference — shared by Slot.schedule
    and Slot.identifier.assigner."""
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_type_user_selected = getattr(
        obj, f"{prefix}_identifier_type_user_selected", None
    )
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if (
        id_use
        or id_type_system
        or id_type_code
        or id_type_text
        or id_system
        or id_value
    ):
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
                    "start": id_period_start.isoformat() if id_period_start else None,
                    "end": id_period_end.isoformat() if id_period_end else None,
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def _fhir_cc(
    coding_system,
    coding_version,
    coding_code,
    coding_display,
    text,
    coding_user_selected,
) -> dict:
    coding = {
        k: v
        for k, v in {
            "system": coding_system,
            "version": coding_version,
            "code": coding_code,
            "display": coding_display,
            "userSelected": coding_user_selected,
        }.items()
        if v is not None
    }
    entry: dict = {}
    if coding:
        entry["coding"] = [coding]
    if text:
        entry["text"] = text
    return entry


def fhir_slot_identifier(i) -> dict:
    """Slot.identifier (Identifier) → FHIR camelCase dict. Resource-specific
    (not the shared app.fhir.datatypes.fhir_identifier) because assigner is a
    resolved Reference(Organization) with an identifier fallback, unlike a
    flat display string."""
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    if i.type_system or i.type_code or i.type_text:
        type_cc: dict = {}
        if i.type_system or i.type_code:
            type_cc["coding"] = [
                {
                    k: v
                    for k, v in {
                        "system": i.type_system,
                        "version": i.type_version,
                        "code": i.type_code,
                        "display": i.type_display,
                        "userSelected": i.type_user_selected,
                    }.items()
                    if v is not None
                }
            ]
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
            for k, v in {
                "start": i.period_start.isoformat() if i.period_start else None,
                "end": i.period_end.isoformat() if i.period_end else None,
            }.items()
            if v
        }
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_slot_service_category(sc) -> dict:
    return _fhir_cc(
        sc.coding_system,
        sc.coding_version,
        sc.coding_code,
        sc.coding_display,
        sc.text,
        sc.coding_user_selected,
    )


def fhir_slot_service_type(st) -> dict:
    return _fhir_cc(
        st.coding_system,
        st.coding_version,
        st.coding_code,
        st.coding_display,
        st.text,
        st.coding_user_selected,
    )


def fhir_slot_specialty(sp) -> dict:
    return _fhir_cc(
        sp.coding_system,
        sp.coding_version,
        sp.coding_code,
        sp.coding_display,
        sp.text,
        sp.coding_user_selected,
    )


def fhir_slot_appointment_type(slot) -> dict:
    """Slot.appointmentType (0..1 CodeableConcept) → FHIR camelCase dict."""
    return _fhir_cc(
        slot.appointment_type_system,
        slot.appointment_type_version,
        slot.appointment_type_code,
        slot.appointment_type_display,
        slot.appointment_type_text,
        slot.appointment_type_user_selected,
    )


def fhir_slot_schedule(slot) -> dict:
    """Slot.schedule (1..1 Reference(Schedule)) → FHIR camelCase dict. Uses
    the shared resolved-reference-plus-fallback renderer even though the
    reference is required — the identifier fallback still applies whenever
    the target isn't resolvable as a same-tenant resource."""
    return _fhir_reference(slot, "schedule")


def to_fhir_slot(slot: SlotModel) -> dict:
    result: dict = {
        "resourceType": "Slot",
        "id": str(slot.slot_id),
    }

    identifiers = [fhir_slot_identifier(i) for i in (slot.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    service_categories = [
        fhir_slot_service_category(sc) for sc in (slot.service_categories or [])
    ]
    if service_categories:
        result["serviceCategory"] = service_categories

    service_types = [fhir_slot_service_type(st) for st in (slot.service_types or [])]
    if service_types:
        result["serviceType"] = service_types

    specialties = [fhir_slot_specialty(sp) for sp in (slot.specialties or [])]
    if specialties:
        result["specialty"] = specialties

    appointment_type = fhir_slot_appointment_type(slot)
    if appointment_type:
        result["appointmentType"] = appointment_type

    schedule = fhir_slot_schedule(slot)
    if schedule:
        result["schedule"] = schedule

    if slot.status:
        result["status"] = fhir_enum(slot.status)

    if slot.start:
        result["start"] = slot.start.isoformat()

    if slot.end:
        result["end"] = slot.end.isoformat()

    if slot.overbooked is not None:
        result["overbooked"] = slot.overbooked

    if slot.comment:
        result["comment"] = slot.comment

    return {k: v for k, v in result.items() if v is not None}
