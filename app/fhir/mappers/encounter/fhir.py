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


def _cc(coding_system, coding_code, coding_display, text=None) -> dict | None:
    coding = {k: v for k, v in {
        "system": coding_system, "code": coding_code, "display": coding_display,
    }.items() if v}
    cc: dict = {}
    if coding:
        cc["coding"] = [coding]
    if text:
        cc["text"] = text
    return cc or None


def _period(start, end) -> dict | None:
    p = {k: v for k, v in {
        "start": start.isoformat() if start else None,
        "end": end.isoformat() if end else None,
    }.items() if v}
    return p or None


def fhir_encounter_identifier(i: "EncounterIdentifier") -> dict:
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
    period = _period(i.period_start, i.period_end)
    if period:
        entry["period"] = period
    if i.assigner:
        entry["assigner"] = {"display": i.assigner}
    return entry


def fhir_encounter_status_history(sh: "EncounterStatusHistory") -> dict:
    return {k: v for k, v in {
        "status": sh.status.value if hasattr(sh.status, "value") else sh.status,
        "period": _period(sh.period_start, sh.period_end),
    }.items() if v}


def fhir_encounter_class_history(ch: "EncounterClassHistory") -> dict:
    entry: dict = {}
    cls = {k: v for k, v in {
        "system": ch.class_system, "version": ch.class_version,
        "code": ch.class_code, "display": ch.class_display,
    }.items() if v}
    if cls:
        entry["class"] = cls
    period = _period(ch.period_start, ch.period_end)
    if period:
        entry["period"] = period
    return entry


def fhir_encounter_type(t: "EncounterType") -> dict | None:
    return _cc(t.coding_system, t.coding_code, t.coding_display, t.text)


def fhir_encounter_episode_of_care(e: "EncounterEpisodeOfCare") -> dict:
    entry: dict = {}
    if e.reference_type and e.reference_id:
        entry["reference"] = f"{e.reference_type.value}/{e.reference_id}"
    if e.reference_display:
        entry["display"] = e.reference_display
    return entry


def fhir_encounter_based_on(b: "EncounterBasedOn") -> dict:
    entry: dict = {}
    if b.reference_type and b.reference_id:
        entry["reference"] = f"{b.reference_type.value}/{b.reference_id}"
    if b.reference_display:
        entry["display"] = b.reference_display
    return entry


def fhir_encounter_participant(p: "EncounterParticipant") -> dict:
    entry: dict = {}
    if p.types:
        type_cc_list = [cc for pt in p.types if (cc := _cc(pt.coding_system, pt.coding_code, pt.coding_display, pt.text))]
        if type_cc_list:
            entry["type"] = type_cc_list
    if p.reference_type and p.reference_id:
        individual: dict = {"reference": f"{p.reference_type.value}/{p.reference_id}"}
        if p.reference_display:
            individual["display"] = p.reference_display
        entry["individual"] = individual
    period = _period(p.period_start, p.period_end)
    if period:
        entry["period"] = period
    return entry


def fhir_encounter_appointment_ref(a: "EncounterAppointmentRef") -> dict:
    entry: dict = {}
    if a.reference_type and a.reference_id:
        entry["reference"] = f"{a.reference_type.value}/{a.reference_id}"
    if a.reference_display:
        entry["display"] = a.reference_display
    return entry


def fhir_encounter_reason_code(rc: "EncounterReasonCode") -> dict | None:
    return _cc(rc.coding_system, rc.coding_code, rc.coding_display, rc.text)


def fhir_encounter_reason_reference(rr: "EncounterReasonReference") -> dict:
    entry: dict = {}
    if rr.reference_type and rr.reference_id:
        entry["reference"] = f"{rr.reference_type.value}/{rr.reference_id}"
    if rr.reference_display:
        entry["display"] = rr.reference_display
    return entry


def fhir_encounter_diagnosis(d: "EncounterDiagnosis") -> dict:
    entry: dict = {}
    if d.condition_type and d.condition_id:
        cond: dict = {"reference": f"{d.condition_type.value}/{d.condition_id}"}
        if d.condition_display:
            cond["display"] = d.condition_display
        entry["condition"] = cond
    use_cc = _cc(d.use_system, d.use_code, d.use_display, d.use_text)
    if use_cc:
        entry["use"] = use_cc
    if d.rank is not None:
        entry["rank"] = d.rank
    return entry


def fhir_encounter_account(a: "EncounterAccount") -> dict:
    entry: dict = {}
    if a.reference_type and a.reference_id:
        entry["reference"] = f"{a.reference_type.value}/{a.reference_id}"
    if a.reference_display:
        entry["display"] = a.reference_display
    return entry


def fhir_encounter_diet_preference(dp: "EncounterDietPreference") -> dict | None:
    return _cc(dp.coding_system, dp.coding_code, dp.coding_display, dp.text)


def fhir_encounter_special_arrangement(sa: "EncounterSpecialArrangement") -> dict | None:
    return _cc(sa.coding_system, sa.coding_code, sa.coding_display, sa.text)


def fhir_encounter_special_courtesy(sc: "EncounterSpecialCourtesy") -> dict | None:
    return _cc(sc.coding_system, sc.coding_code, sc.coding_display, sc.text)


def fhir_encounter_hospitalization(encounter: "EncounterModel") -> dict:
    hosp: dict = {}

    if encounter.hospitalization_pre_admission_identifier_value:
        pre_id: dict = {"value": encounter.hospitalization_pre_admission_identifier_value}
        if encounter.hospitalization_pre_admission_identifier_system:
            pre_id["system"] = encounter.hospitalization_pre_admission_identifier_system
        hosp["preAdmissionIdentifier"] = pre_id

    if encounter.hospitalization_origin_id:
        ref_str = (
            f"{encounter.hospitalization_origin_type}/{encounter.hospitalization_origin_id}"
            if encounter.hospitalization_origin_type
            else f"Location/{encounter.hospitalization_origin_id}"
        )
        orig: dict = {"reference": ref_str}
        if encounter.hospitalization_origin_display:
            orig["display"] = encounter.hospitalization_origin_display
        hosp["origin"] = orig

    for prefix, fhir_key in [
        ("hospitalization_admit_source", "admitSource"),
        ("hospitalization_re_admission", "reAdmission"),
        ("hospitalization_discharge_disposition", "dischargeDisposition"),
    ]:
        cc = _cc(
            getattr(encounter, f"{prefix}_system", None),
            getattr(encounter, f"{prefix}_code", None),
            getattr(encounter, f"{prefix}_display", None),
            getattr(encounter, f"{prefix}_text", None),
        )
        if cc:
            hosp[fhir_key] = cc

    if encounter.diet_preferences:
        dp_list = [cc for dp in encounter.diet_preferences if (cc := fhir_encounter_diet_preference(dp))]
        if dp_list:
            hosp["dietPreference"] = dp_list

    if encounter.special_courtesies:
        sc_list = [cc for sc in encounter.special_courtesies if (cc := fhir_encounter_special_courtesy(sc))]
        if sc_list:
            hosp["specialCourtesy"] = sc_list

    if encounter.special_arrangements:
        sa_list = [cc for sa in encounter.special_arrangements if (cc := fhir_encounter_special_arrangement(sa))]
        if sa_list:
            hosp["specialArrangement"] = sa_list

    if encounter.hospitalization_destination_id:
        ref_str = (
            f"{encounter.hospitalization_destination_type}/{encounter.hospitalization_destination_id}"
            if encounter.hospitalization_destination_type
            else f"Location/{encounter.hospitalization_destination_id}"
        )
        dest: dict = {"reference": ref_str}
        if encounter.hospitalization_destination_display:
            dest["display"] = encounter.hospitalization_destination_display
        hosp["destination"] = dest

    return hosp


def fhir_encounter_location(loc: "EncounterLocation") -> dict:
    entry: dict = {}
    if loc.reference_type and loc.reference_id:
        lref: dict = {"reference": f"{loc.reference_type.value}/{loc.reference_id}"}
        if loc.reference_display:
            lref["display"] = loc.reference_display
        entry["location"] = lref
    if loc.status:
        entry["status"] = loc.status.value if hasattr(loc.status, "value") else loc.status
    physical_type_cc = _cc(loc.physical_type_system, loc.physical_type_code, loc.physical_type_display, loc.physical_type_text)
    if physical_type_cc:
        entry["physicalType"] = physical_type_cc
    period = _period(loc.period_start, loc.period_end)
    if period:
        entry["period"] = period
    return entry


def to_fhir_encounter(encounter: "EncounterModel") -> dict:
    result: dict = {
        "resourceType": "Encounter",
        "id": str(encounter.encounter_id),
        "status": encounter.status.value if encounter.status else None,
    }

    if encounter.identifiers:
        result["identifier"] = [fhir_encounter_identifier(i) for i in encounter.identifiers]

    if encounter.status_history:
        result["statusHistory"] = [fhir_encounter_status_history(sh) for sh in encounter.status_history]

    class_coding = {k: v for k, v in {
        "system": encounter.class_system, "code": encounter.class_code, "display": encounter.class_display,
    }.items() if v}
    if class_coding:
        result["class"] = class_coding

    if encounter.class_history:
        ch_list = [e for ch in encounter.class_history if (e := fhir_encounter_class_history(ch))]
        if ch_list:
            result["classHistory"] = ch_list

    if encounter.types:
        type_list = [cc for t in encounter.types if (cc := fhir_encounter_type(t))]
        if type_list:
            result["type"] = type_list

    service_type_cc = _cc(encounter.service_type_system, encounter.service_type_code,
                           encounter.service_type_display, encounter.service_type_text)
    if service_type_cc:
        result["serviceType"] = service_type_cc

    priority_cc = _cc(encounter.priority_system, encounter.priority_code,
                      encounter.priority_display, encounter.priority_text)
    if priority_cc:
        result["priority"] = priority_cc

    if encounter.subject_type and encounter.subject_id:
        subj: dict = {"reference": f"{encounter.subject_type.value}/{encounter.subject_id}"}
        if encounter.subject_display:
            subj["display"] = encounter.subject_display
        result["subject"] = subj

    if encounter.episode_of_cares:
        eoc_list = [e for e in [fhir_encounter_episode_of_care(ep) for ep in encounter.episode_of_cares] if e]
        if eoc_list:
            result["episodeOfCare"] = eoc_list

    if encounter.based_ons:
        bo_list = [e for e in [fhir_encounter_based_on(b) for b in encounter.based_ons] if e]
        if bo_list:
            result["basedOn"] = bo_list

    if encounter.participants:
        p_list = [e for p in encounter.participants if (e := fhir_encounter_participant(p))]
        if p_list:
            result["participant"] = p_list

    if encounter.appointment_refs:
        appt_list = [e for e in [fhir_encounter_appointment_ref(a) for a in encounter.appointment_refs] if e]
        if appt_list:
            result["appointment"] = appt_list

    period = _period(encounter.period_start, encounter.period_end)
    if period:
        result["period"] = period

    if encounter.length_value is not None or encounter.length_code:
        result["length"] = {k: v for k, v in {
            "value": encounter.length_value,
            "comparator": encounter.length_comparator,
            "unit": encounter.length_unit,
            "system": encounter.length_system,
            "code": encounter.length_code,
        }.items() if v is not None}

    if encounter.reason_codes:
        rc_list = [cc for rc in encounter.reason_codes if (cc := fhir_encounter_reason_code(rc))]
        if rc_list:
            result["reasonCode"] = rc_list

    if encounter.reason_references:
        rr_list = [e for e in [fhir_encounter_reason_reference(rr) for rr in encounter.reason_references] if e]
        if rr_list:
            result["reasonReference"] = rr_list

    if encounter.diagnoses:
        diag_list = [e for d in encounter.diagnoses if (e := fhir_encounter_diagnosis(d))]
        if diag_list:
            result["diagnosis"] = diag_list

    if encounter.accounts:
        acct_list = [e for e in [fhir_encounter_account(a) for a in encounter.accounts] if e]
        if acct_list:
            result["account"] = acct_list

    hospitalization = fhir_encounter_hospitalization(encounter)
    if hospitalization:
        result["hospitalization"] = hospitalization

    if encounter.locations:
        loc_list = [e for loc in encounter.locations if (e := fhir_encounter_location(loc))]
        if loc_list:
            result["location"] = loc_list

    if encounter.service_provider:
        sp: dict = {"reference": f"Organization/{encounter.service_provider.organization_id}"}
        if encounter.service_provider_display:
            sp["display"] = encounter.service_provider_display
        result["serviceProvider"] = sp

    if encounter.part_of:
        result["partOf"] = {"reference": f"Encounter/{encounter.part_of.encounter_id}"}

    return {k: v for k, v in result.items() if v is not None}
