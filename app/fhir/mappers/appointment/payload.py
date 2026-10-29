"""Payload -> FHIR JSON conversion, the mirror image of fhir.py.

fhir.py's to_fhir_appointment() reads a persisted AppointmentModel (ORM row,
post-insert, with resolved child relationships) and is used for GET
responses. This module reads the *validated Pydantic input schema*
(AppointmentCreateSchema / AppointmentPatchSchema) instead, before anything
is written to the DB, so the result can be fed through
app.fhir.validation.validate_resource() at the service layer — mirrors
app.fhir.mappers.slot.payload's docstring/reasoning exactly.

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
    from app.schemas.appointment import AppointmentCreateSchema, AppointmentPatchSchema


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
    fallback — mirrors app.fhir.mappers.slot.payload._reference_from_payload."""
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


def payload_service_category(sc) -> dict:
    return _cc(sc.coding, sc.text)


def payload_service_type(st) -> dict:
    return _cc(st.coding, st.text)


def payload_specialty(sp) -> dict:
    return _cc(sp.coding, sp.text)


def payload_reason_code(rc) -> dict:
    return _cc(rc.coding, rc.text)


def payload_reason_reference(rr) -> dict:
    return _reference_from_payload(rr, "reference")


def payload_supporting_information(si) -> dict:
    return _reference_from_payload(si, "reference")


def payload_slot(s) -> dict:
    return _reference_from_payload(s, "reference")


def payload_based_on(bo) -> dict:
    return _reference_from_payload(bo, "reference")


def payload_requested_period(rp) -> dict:
    return _period(rp.start, rp.end) or {}


def payload_participant_type(pt) -> dict:
    return _cc(pt.coding, pt.text)


# Status is the one field this module intentionally does NOT route through
# fhir_enum() — the input schema's app.schemas.enums enums already carry the
# true hyphenated FHIR code as their .value (see those classes' docstrings),
# unlike the model-layer enums.
def payload_status(status) -> str | None:
    return status.value if status else None


def payload_required(required) -> str | None:
    return required.value if required else None


def payload_participant(p) -> dict:
    entry: dict = {}
    types = [payload_participant_type(t) for t in (p.type or [])]
    types = [t for t in types if t]
    if types:
        entry["type"] = types
    actor = _reference_from_payload(p, "actor")
    if actor:
        entry["actor"] = actor
    required = payload_required(p.required)
    if required:
        entry["required"] = required
    status = payload_status(p.status)
    if status:
        entry["status"] = status
    period = _period(p.period_start, p.period_end)
    if period:
        entry["period"] = period
    return entry


# Every Appointment field that's a 0..* list, mapped to the builder that
# renders one of its items, and to the FHIR camelCase key it lands under —
# shared by both orchestrators below.
_LIST_FIELDS = {
    "identifier": ("identifier", payload_identifier),
    "service_category": ("serviceCategory", payload_service_category),
    "service_type": ("serviceType", payload_service_type),
    "specialty": ("specialty", payload_specialty),
    "reason_code": ("reasonCode", payload_reason_code),
    "reason_reference": ("reasonReference", payload_reason_reference),
    "supporting_information": ("supportingInformation", payload_supporting_information),
    "slot": ("slot", payload_slot),
    "based_on": ("basedOn", payload_based_on),
    "requested_period": ("requestedPeriod", payload_requested_period),
    "participant": ("participant", payload_participant),
}

_CANCELATION_REASON_FIELDS = {"cancelation_reason_coding", "cancelation_reason_text"}
_APPOINTMENT_TYPE_FIELDS = {"appointment_type_coding", "appointment_type_text"}


def payload_to_fhir_appointment(payload: AppointmentCreateSchema) -> dict:
    """Full-resource conversion for CREATE: a create payload represents the
    resource's entire initial state, so every field is considered present —
    unlike patch_fragment_to_fhir_appointment()'s tri-state handling."""
    result: dict = {"resourceType": "Appointment"}

    if payload.extension:
        result["extension"] = list(payload.extension)
    status = payload_status(payload.status)
    if status:
        result["status"] = status
    cancelation_reason = _cc(payload.cancelation_reason_coding, payload.cancelation_reason_text)
    if cancelation_reason:
        result["cancelationReason"] = cancelation_reason
    appointment_type = _cc(payload.appointment_type_coding, payload.appointment_type_text)
    if appointment_type:
        result["appointmentType"] = appointment_type
    if payload.priority is not None:
        result["priority"] = payload.priority
    if payload.description:
        result["description"] = payload.description
    if payload.start:
        result["start"] = payload.start.isoformat()
    if payload.end:
        result["end"] = payload.end.isoformat()
    if payload.minutes_duration is not None:
        result["minutesDuration"] = payload.minutes_duration
    if payload.created:
        result["created"] = payload.created.isoformat()
    if payload.comment:
        result["comment"] = payload.comment
    if payload.patient_instruction:
        result["patientInstruction"] = payload.patient_instruction

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        items = [item for item in items if item]
        if items:
            result[fhir_key] = items

    return result


def patch_fragment_to_fhir_appointment(payload: AppointmentPatchSchema) -> tuple[dict, set[str]]:
    """Converts only the fields a PATCH request actually supplied (per
    `model_fields_set`) into a FHIR-shaped fragment, alongside the set of
    top-level FHIR keys the request touched — mirrors
    app.fhir.mappers.slot.payload.patch_fragment_to_fhir_slot's
    docstring/semantics exactly."""
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = list(payload.extension)
    if "status" in provided:
        touched.add("status")
        status = payload_status(payload.status)
        if status:
            fragment["status"] = status
    if provided & _CANCELATION_REASON_FIELDS:
        touched.add("cancelationReason")
        cancelation_reason = _cc(
            payload.cancelation_reason_coding, payload.cancelation_reason_text
        )
        if cancelation_reason:
            fragment["cancelationReason"] = cancelation_reason
    if provided & _APPOINTMENT_TYPE_FIELDS:
        touched.add("appointmentType")
        appointment_type = _cc(payload.appointment_type_coding, payload.appointment_type_text)
        if appointment_type:
            fragment["appointmentType"] = appointment_type
    if "priority" in provided:
        touched.add("priority")
        if payload.priority is not None:
            fragment["priority"] = payload.priority
    if "description" in provided:
        touched.add("description")
        if payload.description:
            fragment["description"] = payload.description
    if "start" in provided:
        touched.add("start")
        if payload.start:
            fragment["start"] = payload.start.isoformat()
    if "end" in provided:
        touched.add("end")
        if payload.end:
            fragment["end"] = payload.end.isoformat()
    if "minutes_duration" in provided:
        touched.add("minutesDuration")
        if payload.minutes_duration is not None:
            fragment["minutesDuration"] = payload.minutes_duration
    if "created" in provided:
        touched.add("created")
        if payload.created:
            fragment["created"] = payload.created.isoformat()
    if "comment" in provided:
        touched.add("comment")
        if payload.comment:
            fragment["comment"] = payload.comment
    if "patient_instruction" in provided:
        touched.add("patientInstruction")
        if payload.patient_instruction:
            fragment["patientInstruction"] = payload.patient_instruction

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            items = [builder(item) for item in (getattr(payload, field, None) or [])]
            items = [item for item in items if item]
            if items:
                fragment[fhir_key] = items

    return fragment, touched
