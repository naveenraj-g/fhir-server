from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.schedule import ScheduleModel


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback for when the target isn't a resource in this system. Shared by
    Schedule.identifier.assigner and Schedule.actor — mirrors
    app.fhir.mappers.healthcare_service.fhir._fhir_reference."""
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


def fhir_schedule_identifier(i) -> dict:
    """Schedule.identifier (Identifier) → FHIR camelCase dict. Resource-specific
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


def fhir_schedule_service_category(sc) -> dict:
    return _fhir_cc(
        sc.coding_system,
        sc.coding_version,
        sc.coding_code,
        sc.coding_display,
        sc.text,
        sc.coding_user_selected,
    )


def fhir_schedule_service_type(st) -> dict:
    return _fhir_cc(
        st.coding_system,
        st.coding_version,
        st.coding_code,
        st.coding_display,
        st.text,
        st.coding_user_selected,
    )


def fhir_schedule_specialty(sp) -> dict:
    return _fhir_cc(
        sp.coding_system,
        sp.coding_version,
        sp.coding_code,
        sp.coding_display,
        sp.text,
        sp.coding_user_selected,
    )


def fhir_schedule_actor(a) -> dict:
    """Schedule.actor (Reference — polymorphic, dispatched per-item by its own
    reference_type) → FHIR camelCase dict. Uses the shared resolved-reference-
    plus-fallback renderer since a Device actor isn't a modeled resource here —
    the identifier fallback is often the only populated half for that case."""
    return _fhir_reference(a, "reference")


def to_fhir_schedule(sched: ScheduleModel) -> dict:
    result: dict = {
        "resourceType": "Schedule",
        "id": str(sched.schedule_id),
    }

    identifiers = [fhir_schedule_identifier(i) for i in (sched.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    if sched.active is not None:
        result["active"] = sched.active

    service_categories = [
        fhir_schedule_service_category(sc) for sc in (sched.service_categories or [])
    ]
    if service_categories:
        result["serviceCategory"] = service_categories

    service_types = [
        fhir_schedule_service_type(st) for st in (sched.service_types or [])
    ]
    if service_types:
        result["serviceType"] = service_types

    specialties = [fhir_schedule_specialty(sp) for sp in (sched.specialties or [])]
    if specialties:
        result["specialty"] = specialties

    actors = [fhir_schedule_actor(a) for a in (sched.actors or [])]
    if actors:
        result["actor"] = actors

    if sched.planning_horizon_start or sched.planning_horizon_end:
        result["planningHorizon"] = {
            k: v
            for k, v in {
                "start": sched.planning_horizon_start.isoformat()
                if sched.planning_horizon_start
                else None,
                "end": sched.planning_horizon_end.isoformat()
                if sched.planning_horizon_end
                else None,
            }.items()
            if v
        }

    if sched.comment:
        result["comment"] = sched.comment

    return {k: v for k, v in result.items() if v is not None}
