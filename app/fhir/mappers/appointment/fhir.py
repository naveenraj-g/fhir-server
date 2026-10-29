from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.appointment import AppointmentModel


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback for when the target isn't a resource in this system. Shared by every
    flattened Reference field on Appointment (identifier.assigner, participant.actor,
    and the bare reference rows reasonReference/supportingInformation/slot/basedOn,
    each read with prefix="reference") — mirrors app.fhir.mappers.slot.fhir._fhir_reference."""
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
        if id_period_start or id_period_end:
            identifier["period"] = {
                k: v
                for k, v in {
                    "start": fhir_instant(id_period_start),
                    "end": fhir_instant(id_period_end),
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def _fhir_coding_list(codings) -> list[dict]:
    """Render a list of FhirCodingMixin-shaped rows as a FHIR `coding[]`
    array — mirrors app.fhir.mappers.slot.fhir._fhir_coding_list."""
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


def _fhir_cc(codings, text) -> dict:
    """(codings relationship, text) -> FHIR CodeableConcept dict."""
    coding = _fhir_coding_list(codings)
    entry: dict = {}
    if coding:
        entry["coding"] = coding
    if text:
        entry["text"] = text
    return entry


def _fhir_period(start, end) -> dict | None:
    period = {
        k: v
        for k, v in {"start": fhir_instant(start), "end": fhir_instant(end)}.items()
        if v
    }
    return period or None


def fhir_appointment_identifier(i) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = _fhir_cc(i.type_codings, i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    period = _fhir_period(i.period_start, i.period_end)
    if period:
        entry["period"] = period
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_appointment_service_category(sc) -> dict:
    return _fhir_cc(sc.codings, sc.text)


def fhir_appointment_service_type(st) -> dict:
    return _fhir_cc(st.codings, st.text)


def fhir_appointment_specialty(sp) -> dict:
    return _fhir_cc(sp.codings, sp.text)


def fhir_appointment_reason_code(rc) -> dict:
    return _fhir_cc(rc.codings, rc.text)


def fhir_appointment_reason_reference(rr) -> dict:
    return _fhir_reference(rr, "reference")


def fhir_appointment_supporting_information(si) -> dict:
    """supportingInformation's reference_type is a plain String (not an
    Enum) — _fhir_reference's fhir_enum() call handles a plain str
    transparently, same as every Enum member it otherwise receives."""
    return _fhir_reference(si, "reference")


def fhir_appointment_slot(s) -> dict:
    return _fhir_reference(s, "reference")


def fhir_appointment_based_on(bo) -> dict:
    return _fhir_reference(bo, "reference")


def fhir_appointment_requested_period(rp) -> dict:
    return _fhir_period(rp.start, rp.end) or {}


def fhir_appointment_participant_type(pt) -> dict:
    return _fhir_cc(pt.codings, pt.text)


# AppointmentParticipantRequired's/AppointmentParticipationStatus's member
# .value intentionally equals their underscore-only member .name (same
# reasoning as AppointmentStatus/SlotStatus) — the real hyphenated FHIR
# wire codes (`information-only`, `needs-action`) are derived here.
def _fhir_hyphenate(value) -> str | None:
    rendered = fhir_enum(value)
    return rendered.replace("_", "-") if rendered else rendered


def fhir_appointment_participant(p) -> dict:
    entry: dict = {}
    types = [fhir_appointment_participant_type(t) for t in (p.types or [])]
    types = [t for t in types if t]
    if types:
        entry["type"] = types
    actor = _fhir_reference(p, "actor")
    if actor:
        entry["actor"] = actor
    required = _fhir_hyphenate(p.required)
    if required:
        entry["required"] = required
    status = _fhir_hyphenate(p.status)
    if status:
        entry["status"] = status
    period = _fhir_period(p.period_start, p.period_end)
    if period:
        entry["period"] = period
    return entry


# Base URL for this server's own, not-yet-formally-registered extensions —
# same convention as app.fhir.mappers.organization.fhir._EXT_BASE.
_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(appointment: AppointmentModel) -> dict:
    """Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    rendered into Resource.meta — same convention as
    app.fhir.mappers.slot.fhir._fhir_meta. Appointment has no user_id (see
    the model's docstring), so there's no equivalent of a user-scoped
    extension here."""
    meta: dict = {}
    if appointment.updated_at:
        meta["lastUpdated"] = fhir_instant(appointment.updated_at)

    extensions = []
    if appointment.tenant_id:
        extensions.append({"url": f"{_EXT_BASE}/org-id", "valueString": appointment.tenant_id})
    if appointment.created_by:
        extensions.append({"url": f"{_EXT_BASE}/created-by", "valueString": appointment.created_by})
    if appointment.updated_by:
        extensions.append({"url": f"{_EXT_BASE}/updated-by", "valueString": appointment.updated_by})
    if appointment.created_at:
        extensions.append(
            {"url": f"{_EXT_BASE}/created-at", "valueDateTime": fhir_instant(appointment.created_at)}
        )
    if extensions:
        meta["extension"] = extensions

    return meta


def to_fhir_appointment(appointment: AppointmentModel) -> dict:
    result: dict = {
        "resourceType": "Appointment",
        "id": str(appointment.appointment_id),
    }

    meta = _fhir_meta(appointment)
    if meta:
        result["meta"] = meta

    if appointment.extension:
        result["extension"] = list(appointment.extension)

    identifiers = [fhir_appointment_identifier(i) for i in (appointment.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    status = _fhir_hyphenate(appointment.status)
    if status:
        result["status"] = status

    cancelation_reason = _fhir_cc(
        appointment.cancelation_reason_codings, appointment.cancelation_reason_text
    )
    if cancelation_reason:
        result["cancelationReason"] = cancelation_reason

    service_categories = [
        fhir_appointment_service_category(sc) for sc in (appointment.service_categories or [])
    ]
    service_categories = [sc for sc in service_categories if sc]
    if service_categories:
        result["serviceCategory"] = service_categories

    service_types = [fhir_appointment_service_type(st) for st in (appointment.service_types or [])]
    service_types = [st for st in service_types if st]
    if service_types:
        result["serviceType"] = service_types

    specialties = [fhir_appointment_specialty(sp) for sp in (appointment.specialties or [])]
    specialties = [sp for sp in specialties if sp]
    if specialties:
        result["specialty"] = specialties

    appointment_type = _fhir_cc(
        appointment.appointment_type_codings, appointment.appointment_type_text
    )
    if appointment_type:
        result["appointmentType"] = appointment_type

    reason_codes = [fhir_appointment_reason_code(rc) for rc in (appointment.reason_codes or [])]
    reason_codes = [rc for rc in reason_codes if rc]
    if reason_codes:
        result["reasonCode"] = reason_codes

    reason_references = [
        fhir_appointment_reason_reference(rr) for rr in (appointment.reason_references or [])
    ]
    reason_references = [rr for rr in reason_references if rr]
    if reason_references:
        result["reasonReference"] = reason_references

    if appointment.priority is not None:
        result["priority"] = appointment.priority
    if appointment.description:
        result["description"] = appointment.description

    supporting_informations = [
        fhir_appointment_supporting_information(si)
        for si in (appointment.supporting_informations or [])
    ]
    supporting_informations = [si for si in supporting_informations if si]
    if supporting_informations:
        result["supportingInformation"] = supporting_informations

    if appointment.start:
        result["start"] = fhir_instant(appointment.start)
    if appointment.end:
        result["end"] = fhir_instant(appointment.end)
    if appointment.minutes_duration is not None:
        result["minutesDuration"] = appointment.minutes_duration

    slots = [fhir_appointment_slot(s) for s in (appointment.slots or [])]
    slots = [s for s in slots if s]
    if slots:
        result["slot"] = slots

    if appointment.created:
        result["created"] = fhir_instant(appointment.created)
    if appointment.comment:
        result["comment"] = appointment.comment
    if appointment.patient_instruction:
        result["patientInstruction"] = appointment.patient_instruction

    based_ons = [fhir_appointment_based_on(bo) for bo in (appointment.based_ons or [])]
    based_ons = [bo for bo in based_ons if bo]
    if based_ons:
        result["basedOn"] = based_ons

    # participant is 1..* per spec — always present as an array, even when
    # empty (which would itself fail base R4 validation; see
    # app.models.appointment.core.AppointmentModel's docstring for why the
    # minimum isn't a DB constraint).
    result["participant"] = [
        fhir_appointment_participant(p) for p in (appointment.participants or [])
    ]

    requested_periods = [
        fhir_appointment_requested_period(rp) for rp in (appointment.requested_periods or [])
    ]
    requested_periods = [rp for rp in requested_periods if rp]
    if requested_periods:
        result["requestedPeriod"] = requested_periods

    return {k: v for k, v in result.items() if v is not None}
