from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.appointment.appointment import (
        AppointmentModel,
        AppointmentIdentifier,
        AppointmentServiceCategory,
        AppointmentServiceType,
        AppointmentSpecialty,
        AppointmentReasonCode,
        AppointmentReasonReference,
        AppointmentSupportingInformation,
        AppointmentSlot,
        AppointmentBasedOn,
        AppointmentParticipant,
        AppointmentRequestedPeriod,
    )


def _cc(system, code, display, text) -> dict | None:
    coding = {k: v for k, v in {"system": system, "code": code, "display": display}.items() if v}
    result: dict = {}
    if coding:
        result["coding"] = [coding]
    if text:
        result["text"] = text
    return result if result else None


def fhir_appointment_identifier(i: "AppointmentIdentifier") -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = i.use
    type_cc = _cc(i.type_system, i.type_code, i.type_display, i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        entry["period"] = {k: v for k, v in {
            "start": i.period_start.isoformat() if i.period_start else None,
            "end": i.period_end.isoformat() if i.period_end else None,
        }.items() if v}
    if i.assigner:
        entry["assigner"] = {"display": i.assigner}
    return entry


def fhir_appointment_service_category(sc: "AppointmentServiceCategory") -> dict | None:
    return _cc(sc.coding_system, sc.coding_code, sc.coding_display, sc.text)


def fhir_appointment_service_type(st: "AppointmentServiceType") -> dict | None:
    return _cc(st.coding_system, st.coding_code, st.coding_display, st.text)


def fhir_appointment_specialty(sp: "AppointmentSpecialty") -> dict | None:
    return _cc(sp.coding_system, sp.coding_code, sp.coding_display, sp.text)


def fhir_appointment_reason_code(rc: "AppointmentReasonCode") -> dict | None:
    return _cc(rc.coding_system, rc.coding_code, rc.coding_display, rc.text)


def fhir_appointment_reason_reference(rr: "AppointmentReasonReference") -> dict:
    return {k: v for k, v in {
        "reference": f"{rr.reference_type.value}/{rr.reference_id}" if rr.reference_type and rr.reference_id else None,
        "display": rr.reference_display,
    }.items() if v}


def fhir_appointment_supporting_info(si: "AppointmentSupportingInformation") -> dict:
    entry: dict = {}
    if si.reference_type and si.reference_id:
        entry["reference"] = f"{si.reference_type}/{si.reference_id}"
    if si.reference_display:
        entry["display"] = si.reference_display
    return entry


def fhir_appointment_slot(s: "AppointmentSlot") -> dict:
    return {k: v for k, v in {
        "reference": f"{s.reference_type.value}/{s.reference_id}" if s.reference_type and s.reference_id else None,
        "display": s.reference_display,
    }.items() if v}


def fhir_appointment_based_on(b: "AppointmentBasedOn") -> dict:
    return {k: v for k, v in {
        "reference": f"{b.reference_type.value}/{b.reference_id}" if b.reference_type and b.reference_id else None,
        "display": b.reference_display,
    }.items() if v}


def fhir_appointment_participant(p: "AppointmentParticipant") -> dict:
    entry: dict = {"status": p.status.value if hasattr(p.status, "value") else p.status}
    if p.types:
        type_list = [cc for t in p.types if (cc := _cc(t.coding_system, t.coding_code, t.coding_display, t.text))]
        if type_list:
            entry["type"] = type_list
    if p.reference_type and p.reference_id:
        actor: dict = {"reference": f"{p.reference_type.value}/{p.reference_id}"}
        if p.reference_display:
            actor["display"] = p.reference_display
        entry["actor"] = actor
    if p.required is not None:
        entry["required"] = p.required.value if hasattr(p.required, "value") else p.required
    if p.period_start or p.period_end:
        entry["period"] = {k: v for k, v in {
            "start": p.period_start.isoformat() if p.period_start else None,
            "end": p.period_end.isoformat() if p.period_end else None,
        }.items() if v}
    return entry


def fhir_appointment_requested_period(rp: "AppointmentRequestedPeriod") -> dict:
    return {k: v for k, v in {
        "start": rp.period_start.isoformat() if rp.period_start else None,
        "end": rp.period_end.isoformat() if rp.period_end else None,
    }.items() if v}


def to_fhir_appointment(appointment: "AppointmentModel") -> dict:
    result: dict = {
        "resourceType": "Appointment",
        "id": str(appointment.appointment_id),
        "status": appointment.status.value if hasattr(appointment.status, "value") else appointment.status,
    }

    if appointment.identifiers:
        result["identifier"] = [fhir_appointment_identifier(i) for i in appointment.identifiers]

    cancelation_cc = _cc(
        appointment.cancelation_reason_system,
        appointment.cancelation_reason_code,
        appointment.cancelation_reason_display,
        appointment.cancelation_reason_text,
    )
    if cancelation_cc:
        result["cancelationReason"] = cancelation_cc

    if appointment.service_categories:
        sc_list = [cc for sc in appointment.service_categories if (cc := fhir_appointment_service_category(sc))]
        if sc_list:
            result["serviceCategory"] = sc_list

    if appointment.service_types:
        st_list = [cc for st in appointment.service_types if (cc := fhir_appointment_service_type(st))]
        if st_list:
            result["serviceType"] = st_list

    if appointment.specialties:
        sp_list = [cc for sp in appointment.specialties if (cc := fhir_appointment_specialty(sp))]
        if sp_list:
            result["specialty"] = sp_list

    appt_type_cc = _cc(
        appointment.appointment_type_system,
        appointment.appointment_type_code,
        appointment.appointment_type_display,
        appointment.appointment_type_text,
    )
    if appt_type_cc:
        result["appointmentType"] = appt_type_cc

    if appointment.reason_codes:
        rc_list = [cc for rc in appointment.reason_codes if (cc := fhir_appointment_reason_code(rc))]
        if rc_list:
            result["reasonCode"] = rc_list

    if appointment.reason_references:
        rr_list = [e for e in [fhir_appointment_reason_reference(rr) for rr in appointment.reason_references] if e]
        if rr_list:
            result["reasonReference"] = rr_list

    if appointment.priority is not None:
        result["priority"] = appointment.priority

    if appointment.description:
        result["description"] = appointment.description

    if appointment.supporting_informations:
        si_list = [e for si in appointment.supporting_informations if (e := fhir_appointment_supporting_info(si))]
        if si_list:
            result["supportingInformation"] = si_list

    if appointment.start:
        result["start"] = appointment.start.isoformat()
    if appointment.end:
        result["end"] = appointment.end.isoformat()
    if appointment.minutes_duration is not None:
        result["minutesDuration"] = appointment.minutes_duration

    if appointment.slots:
        result["slot"] = [fhir_appointment_slot(s) for s in appointment.slots]

    if appointment.created:
        result["created"] = appointment.created.isoformat()

    if appointment.comment:
        result["comment"] = appointment.comment

    if appointment.patient_instruction:
        result["patientInstruction"] = appointment.patient_instruction

    if appointment.based_ons:
        result["basedOn"] = [fhir_appointment_based_on(b) for b in appointment.based_ons]

    if appointment.requested_periods:
        periods = [e for rp in appointment.requested_periods if (e := fhir_appointment_requested_period(rp))]
        if periods:
            result["requestedPeriod"] = periods

    result["participant"] = [fhir_appointment_participant(p) for p in appointment.participants]

    # recurrenceTemplate is operational only (not a FHIR R4/R5 core element) — plain-JSON output only.

    return {k: v for k, v in result.items() if v is not None}
