"""Payload -> FHIR JSON conversion, the mirror image of fhir.py.

fhir.py's to_fhir_appointment_response() reads a persisted
AppointmentResponseModel (ORM row, post-insert, with resolved child
relationships) and is used for GET responses. This module reads the
*validated Pydantic input schema* (AppointmentResponseCreateSchema /
AppointmentResponsePatchSchema) instead, before anything is written to the
DB, so the result can be fed through app.fhir.validation.validate_resource()
at the service layer — mirrors app.fhir.mappers.appointment.payload's
docstring/reasoning exactly.

The two can't fully share code: the input schema has no resolved
{prefix}_type/{prefix}_id for a Reference field yet (that's only known
after RESOURCE_REGISTRY's existence check, which happens at write time) —
only the raw `{prefix}` string the caller supplied, plus display/
identifier-fallback fields. Everything else (coding lists, CodeableConcept)
is structurally identical, so those builders are deliberately written
parallel to fhir.py's, field-for-field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.appointment_response import (
        AppointmentResponseCreateSchema,
        AppointmentResponsePatchSchema,
    )


def _coding_list(codings) -> list[dict]:
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


def _cc(codings, text) -> dict:
    coding = _coding_list(codings)
    entry: dict = {}
    if coding:
        entry["coding"] = coding
    if text:
        entry["text"] = text
    return entry


def _period(start, end) -> dict | None:
    period = {
        k: v
        for k, v in {
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
        }.items()
        if v
    }
    return period or None


def _reference_from_payload(obj, prefix: str) -> dict:
    """Builds a FHIR Reference dict from an input-schema object's raw
    `{prefix}` string (the literal value as submitted — never resolved here)
    plus `{prefix}_display` and the `{prefix}_identifier_*` logical-reference
    fallback — mirrors app.fhir.mappers.appointment.payload._reference_from_payload."""
    raw_reference = getattr(obj, prefix, None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    if display:
        entry["display"] = display

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
        period = _period(id_period_start, id_period_end)
        if period:
            identifier["period"] = period
        entry["identifier"] = identifier
    return entry


def payload_identifier(i) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = _cc(i.type_coding, i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    period = _period(i.period_start, i.period_end)
    if period:
        entry["period"] = period
    assigner = _reference_from_payload(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def payload_participant_type(pt) -> dict:
    return _cc(pt.coding, pt.text)


# Status is the one field this module intentionally does NOT route through
# fhir_enum() — the input schema's app.schemas.enums.AppointmentResponseParticipantStatus
# already carries the true hyphenated FHIR code as its .value (see that
# class's docstring), unlike the model-layer enum.
def payload_status(status) -> str | None:
    return status.value if status else None


# Every AppointmentResponse field that's a 0..* list, mapped to the
# builder that renders one of its items, and to the FHIR camelCase key it
# lands under — shared by both orchestrators below.
_LIST_FIELDS = {
    "identifier": ("identifier", payload_identifier),
    "participant_type": ("participantType", payload_participant_type),
}


def payload_to_fhir_appointment_response(payload: AppointmentResponseCreateSchema) -> dict:
    """Full-resource conversion for CREATE: a create payload represents the
    resource's entire initial state, so every field is considered present —
    unlike patch_fragment_to_fhir_appointment_response()'s tri-state handling."""
    result: dict = {"resourceType": "AppointmentResponse"}

    if payload.extension:
        result["extension"] = list(payload.extension)
    appointment = _reference_from_payload(payload, "appointment")
    if appointment:
        result["appointment"] = appointment
    if payload.start:
        result["start"] = payload.start.isoformat()
    if payload.end:
        result["end"] = payload.end.isoformat()
    actor = _reference_from_payload(payload, "actor")
    if actor:
        result["actor"] = actor
    status = payload_status(payload.participant_status)
    if status:
        result["participantStatus"] = status
    if payload.comment:
        result["comment"] = payload.comment

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        items = [item for item in items if item]
        if items:
            result[fhir_key] = items

    return result


def patch_fragment_to_fhir_appointment_response(
    payload: AppointmentResponsePatchSchema,
) -> tuple[dict, set[str]]:
    """Converts only the fields a PATCH request actually supplied (per
    `model_fields_set`) into a FHIR-shaped fragment, alongside the set of
    top-level FHIR keys the request touched — mirrors
    app.fhir.mappers.appointment.payload.patch_fragment_to_fhir_appointment's
    docstring/semantics exactly."""
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = list(payload.extension)
    if provided & {
        "appointment", "appointment_display",
        "appointment_identifier_use", "appointment_identifier_type_system",
        "appointment_identifier_type_version", "appointment_identifier_type_code",
        "appointment_identifier_type_display", "appointment_identifier_type_text",
        "appointment_identifier_type_user_selected", "appointment_identifier_system",
        "appointment_identifier_value", "appointment_identifier_period_start",
        "appointment_identifier_period_end",
    }:
        touched.add("appointment")
        appointment = _reference_from_payload(payload, "appointment")
        if appointment:
            fragment["appointment"] = appointment
    if "start" in provided:
        touched.add("start")
        if payload.start:
            fragment["start"] = payload.start.isoformat()
    if "end" in provided:
        touched.add("end")
        if payload.end:
            fragment["end"] = payload.end.isoformat()
    if provided & {
        "actor", "actor_display",
        "actor_identifier_use", "actor_identifier_type_system",
        "actor_identifier_type_version", "actor_identifier_type_code",
        "actor_identifier_type_display", "actor_identifier_type_text",
        "actor_identifier_type_user_selected", "actor_identifier_system",
        "actor_identifier_value", "actor_identifier_period_start",
        "actor_identifier_period_end",
    }:
        touched.add("actor")
        actor = _reference_from_payload(payload, "actor")
        if actor:
            fragment["actor"] = actor
    if "participant_status" in provided:
        touched.add("participantStatus")
        status = payload_status(payload.participant_status)
        if status:
            fragment["participantStatus"] = status
    if "comment" in provided:
        touched.add("comment")
        if payload.comment:
            fragment["comment"] = payload.comment

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            items = [builder(item) for item in (getattr(payload, field, None) or [])]
            items = [item for item in items if item]
            if items:
                fragment[fhir_key] = items

    return fragment, touched
