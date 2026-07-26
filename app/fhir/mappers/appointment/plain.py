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
        AppointmentRecurrenceTemplate,
    )


def plain_appointment_identifier(i: "AppointmentIdentifier") -> dict:
    return {
        "id": i.id,
        "use": i.use,
        "type_system": i.type_system,
        "type_code": i.type_code,
        "type_display": i.type_display,
        "type_text": i.type_text,
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start.isoformat() if i.period_start else None,
        "period_end": i.period_end.isoformat() if i.period_end else None,
        "assigner": i.assigner,
    }


def plain_appointment_service_category(sc: "AppointmentServiceCategory") -> dict:
    return {
        "id": sc.id,
        "coding_system": sc.coding_system,
        "coding_code": sc.coding_code,
        "coding_display": sc.coding_display,
        "text": sc.text,
    }


def plain_appointment_service_type(st: "AppointmentServiceType") -> dict:
    return {
        "id": st.id,
        "coding_system": st.coding_system,
        "coding_code": st.coding_code,
        "coding_display": st.coding_display,
        "text": st.text,
    }


def plain_appointment_specialty(sp: "AppointmentSpecialty") -> dict:
    return {
        "id": sp.id,
        "coding_system": sp.coding_system,
        "coding_code": sp.coding_code,
        "coding_display": sp.coding_display,
        "text": sp.text,
    }


def plain_appointment_reason_code(rc: "AppointmentReasonCode") -> dict:
    return {
        "id": rc.id,
        "coding_system": rc.coding_system,
        "coding_code": rc.coding_code,
        "coding_display": rc.coding_display,
        "text": rc.text,
    }


def plain_appointment_reason_reference(rr: "AppointmentReasonReference") -> dict:
    return {
        "id": rr.id,
        "reference_type": rr.reference_type.value if rr.reference_type else None,
        "reference_id": rr.reference_id,
        "reference_display": rr.reference_display,
    }


def plain_appointment_supporting_info(si: "AppointmentSupportingInformation") -> dict:
    return {
        "id": si.id,
        "reference_type": si.reference_type,
        "reference_id": si.reference_id,
        "reference_display": si.reference_display,
    }


def plain_appointment_slot(s: "AppointmentSlot") -> dict:
    return {
        "id": s.id,
        "reference_type": s.reference_type.value if s.reference_type else None,
        "reference_id": s.reference_id,
        "reference_display": s.reference_display,
    }


def plain_appointment_based_on(b: "AppointmentBasedOn") -> dict:
    return {
        "id": b.id,
        "reference_type": b.reference_type.value if b.reference_type else None,
        "reference_id": b.reference_id,
        "reference_display": b.reference_display,
    }


def plain_appointment_participant(p: "AppointmentParticipant") -> dict:
    entry: dict = {
        "id": p.id,
        "reference_type": p.reference_type.value if p.reference_type else None,
        "reference_id": p.reference_id,
        "reference_display": p.reference_display,
        "required": p.required.value if p.required else None,
        "status": p.status.value if hasattr(p.status, "value") else p.status,
        "period_start": p.period_start.isoformat() if p.period_start else None,
        "period_end": p.period_end.isoformat() if p.period_end else None,
    }
    if p.types:
        entry["types"] = [
            {"coding_system": t.coding_system, "coding_code": t.coding_code,
             "coding_display": t.coding_display, "text": t.text}
            for t in p.types
        ]
    return entry


def plain_appointment_requested_period(rp: "AppointmentRequestedPeriod") -> dict:
    return {
        "id": rp.id,
        "period_start": rp.period_start.isoformat() if rp.period_start else None,
        "period_end": rp.period_end.isoformat() if rp.period_end else None,
    }


def plain_appointment_recurrence_template(rt: "AppointmentRecurrenceTemplate") -> dict:
    rt_plain: dict = {
        "recurrence_type_code": rt.recurrence_type_code,
        "recurrence_type_display": rt.recurrence_type_display,
        "recurrence_type_system": rt.recurrence_type_system,
        "timezone_code": rt.timezone_code,
        "timezone_display": rt.timezone_display,
        "last_occurrence_date": rt.last_occurrence_date.isoformat() if rt.last_occurrence_date else None,
        "occurrence_count": rt.occurrence_count,
        "occurrence_dates": [d for d in rt.occurrence_dates.split(",") if d] if rt.occurrence_dates else None,
        "excluding_dates": [d for d in rt.excluding_dates.split(",") if d] if rt.excluding_dates else None,
        "excluding_recurrence_ids": (
            [int(i) for i in rt.excluding_recurrence_ids.split(",") if i]
            if rt.excluding_recurrence_ids else None
        ),
    }

    weekly = {k: v for k, v in {
        "monday": rt.weekly_monday, "tuesday": rt.weekly_tuesday,
        "wednesday": rt.weekly_wednesday, "thursday": rt.weekly_thursday,
        "friday": rt.weekly_friday, "saturday": rt.weekly_saturday,
        "sunday": rt.weekly_sunday, "week_interval": rt.weekly_week_interval,
    }.items() if v is not None}
    rt_plain["weekly_template"] = weekly if weekly else None

    monthly = {k: v for k, v in {
        "day_of_month": rt.monthly_day_of_month,
        "nth_week_code": rt.monthly_nth_week_code,
        "nth_week_display": rt.monthly_nth_week_display,
        "day_of_week_code": rt.monthly_day_of_week_code,
        "day_of_week_display": rt.monthly_day_of_week_display,
        "month_interval": rt.monthly_month_interval,
    }.items() if v is not None}
    rt_plain["monthly_template"] = monthly if monthly else None

    rt_plain["yearly_template"] = (
        {"year_interval": rt.yearly_year_interval} if rt.yearly_year_interval is not None else None
    )

    return {k: v for k, v in rt_plain.items() if v is not None}


def to_plain_appointment(appointment: "AppointmentModel") -> dict:
    result: dict = {
        "id": appointment.appointment_id,
        "user_id": appointment.user_id,
        "org_id": appointment.org_id,
        "status": appointment.status.value if hasattr(appointment.status, "value") else appointment.status,
        "cancelation_reason_system": appointment.cancelation_reason_system,
        "cancelation_reason_code": appointment.cancelation_reason_code,
        "cancelation_reason_display": appointment.cancelation_reason_display,
        "cancelation_reason_text": appointment.cancelation_reason_text,
        "appointment_type_system": appointment.appointment_type_system,
        "appointment_type_code": appointment.appointment_type_code,
        "appointment_type_display": appointment.appointment_type_display,
        "appointment_type_text": appointment.appointment_type_text,
        "priority": appointment.priority,
        "start": appointment.start.isoformat() if appointment.start else None,
        "end": appointment.end.isoformat() if appointment.end else None,
        "minutes_duration": appointment.minutes_duration,
        "created": appointment.created.isoformat() if appointment.created else None,
        "description": appointment.description,
        "comment": appointment.comment,
        "patient_instruction": appointment.patient_instruction,
        "created_at": appointment.created_at.isoformat() if appointment.created_at else None,
        "updated_at": appointment.updated_at.isoformat() if appointment.updated_at else None,
        "created_by": appointment.created_by,
        "updated_by": appointment.updated_by,
    }

    if appointment.identifiers:
        result["identifier"] = [plain_appointment_identifier(i) for i in appointment.identifiers]
    if appointment.service_categories:
        result["service_category"] = [plain_appointment_service_category(sc) for sc in appointment.service_categories]
    if appointment.service_types:
        result["service_type"] = [plain_appointment_service_type(st) for st in appointment.service_types]
    if appointment.specialties:
        result["specialty"] = [plain_appointment_specialty(sp) for sp in appointment.specialties]
    if appointment.reason_codes:
        result["reason_code"] = [plain_appointment_reason_code(rc) for rc in appointment.reason_codes]
    if appointment.reason_references:
        result["reason_reference"] = [plain_appointment_reason_reference(rr) for rr in appointment.reason_references]
    if appointment.supporting_informations:
        result["supporting_information"] = [plain_appointment_supporting_info(si) for si in appointment.supporting_informations]
    if appointment.slots:
        result["slot"] = [plain_appointment_slot(s) for s in appointment.slots]
    if appointment.based_ons:
        result["based_on"] = [plain_appointment_based_on(b) for b in appointment.based_ons]
    if appointment.participants:
        result["participant"] = [plain_appointment_participant(p) for p in appointment.participants]
    if appointment.requested_periods:
        result["requested_period"] = [plain_appointment_requested_period(rp) for rp in appointment.requested_periods]

    if appointment.recurrence_template:
        result["recurrence_template"] = plain_appointment_recurrence_template(appointment.recurrence_template)

    return {k: v for k, v in result.items() if v is not None}
