from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.encounter.encounter import (
        EncounterModel,
        EncounterIdentifier,
        EncounterStatusHistory,
        EncounterClassHistory,
        EncounterType,
        EncounterEpisodeOfCare,
        EncounterBasedOn,
        EncounterParticipant,
        EncounterAppointmentRef,
        EncounterReasonCode,
        EncounterReasonReference,
        EncounterDiagnosis,
        EncounterAccount,
        EncounterDietPreference,
        EncounterSpecialArrangement,
        EncounterSpecialCourtesy,
        EncounterLocation,
    )


def plain_encounter_identifier(i: "EncounterIdentifier") -> dict:
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


def plain_encounter_status_history(sh: "EncounterStatusHistory") -> dict:
    return {
        "id": sh.id,
        "status": sh.status.value if hasattr(sh.status, "value") else sh.status,
        "period_start": sh.period_start.isoformat() if sh.period_start else None,
        "period_end": sh.period_end.isoformat() if sh.period_end else None,
    }


def plain_encounter_class_history(ch: "EncounterClassHistory") -> dict:
    return {
        "id": ch.id,
        "class_system": ch.class_system,
        "class_version": ch.class_version,
        "class_code": ch.class_code,
        "class_display": ch.class_display,
        "period_start": ch.period_start.isoformat() if ch.period_start else None,
        "period_end": ch.period_end.isoformat() if ch.period_end else None,
    }


def plain_encounter_type(t: "EncounterType") -> dict:
    return {
        "id": t.id,
        "coding_system": t.coding_system,
        "coding_code": t.coding_code,
        "coding_display": t.coding_display,
        "text": t.text,
    }


def plain_encounter_episode_of_care(e: "EncounterEpisodeOfCare") -> dict:
    return {
        "id": e.id,
        "reference_type": e.reference_type.value if e.reference_type else None,
        "reference_id": e.reference_id,
        "reference_display": e.reference_display,
    }


def plain_encounter_based_on(b: "EncounterBasedOn") -> dict:
    return {
        "id": b.id,
        "reference_type": b.reference_type.value if b.reference_type else None,
        "reference_id": b.reference_id,
        "reference_display": b.reference_display,
    }


def plain_encounter_participant(p: "EncounterParticipant") -> dict:
    entry: dict = {
        "id": p.id,
        "reference_type": p.reference_type.value if p.reference_type else None,
        "reference_id": p.reference_id,
        "reference_display": p.reference_display,
        "period_start": p.period_start.isoformat() if p.period_start else None,
        "period_end": p.period_end.isoformat() if p.period_end else None,
    }
    if p.types:
        entry["type"] = [
            {"coding_system": pt.coding_system, "coding_code": pt.coding_code,
             "coding_display": pt.coding_display, "text": pt.text}
            for pt in p.types
        ]
    return entry


def plain_encounter_appointment_ref(a: "EncounterAppointmentRef") -> dict:
    return {
        "id": a.id,
        "reference_type": a.reference_type.value if a.reference_type else None,
        "reference_id": a.reference_id,
        "reference_display": a.reference_display,
    }


def plain_encounter_reason_code(rc: "EncounterReasonCode") -> dict:
    return {
        "id": rc.id,
        "coding_system": rc.coding_system,
        "coding_code": rc.coding_code,
        "coding_display": rc.coding_display,
        "text": rc.text,
    }


def plain_encounter_reason_reference(rr: "EncounterReasonReference") -> dict:
    return {
        "id": rr.id,
        "reference_type": rr.reference_type.value if rr.reference_type else None,
        "reference_id": rr.reference_id,
        "reference_display": rr.reference_display,
    }


def plain_encounter_diagnosis(d: "EncounterDiagnosis") -> dict:
    return {
        "id": d.id,
        "condition_type": d.condition_type.value if d.condition_type else None,
        "condition_id": d.condition_id,
        "condition_display": d.condition_display,
        "use_system": d.use_system,
        "use_code": d.use_code,
        "use_display": d.use_display,
        "use_text": d.use_text,
        "rank": d.rank,
    }


def plain_encounter_account(a: "EncounterAccount") -> dict:
    return {
        "id": a.id,
        "reference_type": a.reference_type.value if a.reference_type else None,
        "reference_id": a.reference_id,
        "reference_display": a.reference_display,
    }


def plain_encounter_diet_preference(dp: "EncounterDietPreference") -> dict:
    return {
        "id": dp.id,
        "coding_system": dp.coding_system,
        "coding_code": dp.coding_code,
        "coding_display": dp.coding_display,
        "text": dp.text,
    }


def plain_encounter_special_arrangement(sa: "EncounterSpecialArrangement") -> dict:
    return {
        "id": sa.id,
        "coding_system": sa.coding_system,
        "coding_code": sa.coding_code,
        "coding_display": sa.coding_display,
        "text": sa.text,
    }


def plain_encounter_special_courtesy(sc: "EncounterSpecialCourtesy") -> dict:
    return {
        "id": sc.id,
        "coding_system": sc.coding_system,
        "coding_code": sc.coding_code,
        "coding_display": sc.coding_display,
        "text": sc.text,
    }


def plain_encounter_location(loc: "EncounterLocation") -> dict:
    return {
        "id": loc.id,
        "reference_type": loc.reference_type.value if loc.reference_type else None,
        "reference_id": loc.reference_id,
        "reference_display": loc.reference_display,
        "status": loc.status.value if loc.status else None,
        "physical_type_system": loc.physical_type_system,
        "physical_type_code": loc.physical_type_code,
        "physical_type_display": loc.physical_type_display,
        "physical_type_text": loc.physical_type_text,
        "period_start": loc.period_start.isoformat() if loc.period_start else None,
        "period_end": loc.period_end.isoformat() if loc.period_end else None,
    }


def plain_encounter_hospitalization(encounter: "EncounterModel") -> dict:
    return {
        "pre_admission_identifier_system": encounter.hospitalization_pre_admission_identifier_system,
        "pre_admission_identifier_value": encounter.hospitalization_pre_admission_identifier_value,
        "origin_type": encounter.hospitalization_origin_type,
        "origin_id": encounter.hospitalization_origin_id,
        "origin_display": encounter.hospitalization_origin_display,
        "admit_source_system": encounter.hospitalization_admit_source_system,
        "admit_source_code": encounter.hospitalization_admit_source_code,
        "admit_source_display": encounter.hospitalization_admit_source_display,
        "admit_source_text": encounter.hospitalization_admit_source_text,
        "re_admission_system": encounter.hospitalization_re_admission_system,
        "re_admission_code": encounter.hospitalization_re_admission_code,
        "re_admission_display": encounter.hospitalization_re_admission_display,
        "re_admission_text": encounter.hospitalization_re_admission_text,
        "diet_preference": [plain_encounter_diet_preference(dp) for dp in encounter.diet_preferences] or None,
        "special_courtesy": [plain_encounter_special_courtesy(sc) for sc in encounter.special_courtesies] or None,
        "special_arrangement": [plain_encounter_special_arrangement(sa) for sa in encounter.special_arrangements] or None,
        "destination_type": encounter.hospitalization_destination_type,
        "destination_id": encounter.hospitalization_destination_id,
        "destination_display": encounter.hospitalization_destination_display,
        "discharge_disposition_system": encounter.hospitalization_discharge_disposition_system,
        "discharge_disposition_code": encounter.hospitalization_discharge_disposition_code,
        "discharge_disposition_display": encounter.hospitalization_discharge_disposition_display,
        "discharge_disposition_text": encounter.hospitalization_discharge_disposition_text,
    }


def to_plain_encounter(encounter: "EncounterModel") -> dict:
    result: dict = {
        "id": encounter.encounter_id,
        "user_id": encounter.user_id,
        "org_id": encounter.org_id,
        "status": encounter.status.value if encounter.status else None,
        "class_system": encounter.class_system,
        "class_code": encounter.class_code,
        "class_display": encounter.class_display,
        "service_type_system": encounter.service_type_system,
        "service_type_code": encounter.service_type_code,
        "service_type_display": encounter.service_type_display,
        "service_type_text": encounter.service_type_text,
        "priority_system": encounter.priority_system,
        "priority_code": encounter.priority_code,
        "priority_display": encounter.priority_display,
        "priority_text": encounter.priority_text,
        "subject_type": encounter.subject_type.value if encounter.subject_type else None,
        "subject_id": encounter.subject_id,
        "subject_display": encounter.subject_display,
        "period_start": encounter.period_start.isoformat() if encounter.period_start else None,
        "period_end": encounter.period_end.isoformat() if encounter.period_end else None,
        "service_provider_type": encounter.service_provider_type.value if encounter.service_provider_type else None,
        "service_provider_id": encounter.service_provider.organization_id if encounter.service_provider else None,
        "service_provider_display": encounter.service_provider_display,
        "part_of_id": encounter.part_of.encounter_id if encounter.part_of else None,
        "created_at": encounter.created_at.isoformat() if encounter.created_at else None,
        "updated_at": encounter.updated_at.isoformat() if encounter.updated_at else None,
        "created_by": encounter.created_by,
        "updated_by": encounter.updated_by,
    }

    if encounter.length_value is not None or encounter.length_code:
        result["length"] = {
            "value": encounter.length_value,
            "comparator": encounter.length_comparator,
            "unit": encounter.length_unit,
            "system": encounter.length_system,
            "code": encounter.length_code,
        }

    hospitalization_fields = [
        "hospitalization_pre_admission_identifier_system", "hospitalization_pre_admission_identifier_value",
        "hospitalization_origin_type", "hospitalization_origin_id", "hospitalization_origin_display",
        "hospitalization_admit_source_system", "hospitalization_admit_source_code",
        "hospitalization_admit_source_display", "hospitalization_admit_source_text",
        "hospitalization_re_admission_system", "hospitalization_re_admission_code",
        "hospitalization_re_admission_display", "hospitalization_re_admission_text",
        "hospitalization_destination_type", "hospitalization_destination_id", "hospitalization_destination_display",
        "hospitalization_discharge_disposition_system", "hospitalization_discharge_disposition_code",
        "hospitalization_discharge_disposition_display", "hospitalization_discharge_disposition_text",
    ]
    if any(getattr(encounter, f, None) for f in hospitalization_fields) or encounter.diet_preferences or encounter.special_arrangements or encounter.special_courtesies:
        result["hospitalization"] = plain_encounter_hospitalization(encounter)

    if encounter.identifiers:
        result["identifier"] = [plain_encounter_identifier(i) for i in encounter.identifiers]
    if encounter.status_history:
        result["status_history"] = [plain_encounter_status_history(sh) for sh in encounter.status_history]
    if encounter.class_history:
        result["class_history"] = [plain_encounter_class_history(ch) for ch in encounter.class_history]
    if encounter.types:
        result["type"] = [plain_encounter_type(t) for t in encounter.types]
    if encounter.episode_of_cares:
        result["episode_of_care"] = [plain_encounter_episode_of_care(e) for e in encounter.episode_of_cares]
    if encounter.based_ons:
        result["based_on"] = [plain_encounter_based_on(b) for b in encounter.based_ons]
    if encounter.participants:
        result["participant"] = [plain_encounter_participant(p) for p in encounter.participants]
    if encounter.appointment_refs:
        result["appointment"] = [plain_encounter_appointment_ref(a) for a in encounter.appointment_refs]
    if encounter.reason_codes:
        result["reason_code"] = [plain_encounter_reason_code(rc) for rc in encounter.reason_codes]
    if encounter.reason_references:
        result["reason_reference"] = [plain_encounter_reason_reference(rr) for rr in encounter.reason_references]
    if encounter.diagnoses:
        result["diagnosis"] = [plain_encounter_diagnosis(d) for d in encounter.diagnoses]
    if encounter.accounts:
        result["account"] = [plain_encounter_account(a) for a in encounter.accounts]
    if encounter.locations:
        result["location"] = [plain_encounter_location(loc) for loc in encounter.locations]

    return {k: v for k, v in result.items() if v is not None}
