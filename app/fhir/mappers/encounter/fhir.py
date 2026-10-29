from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.encounter import EncounterModel


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback — mirrors app.fhir.mappers.appointment.fhir._fhir_reference."""
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


def _fhir_single_coding(obj) -> dict:
    """Build a bare FHIR Coding dict (system/version/code/display/
    userSelected) from a FhirCodingMixin-shaped row — used for
    Encounter.class / Encounter.classHistory.class, the first bare-Coding
    (not CodeableConcept) fields in this codebase. Deliberately reads the
    BARE attribute names (`obj.system`, not `obj.class_system`) —
    FhirCodingMixin's `_coding_prefix` only renames the underlying DB
    column, never the Python attribute — see
    app.repository.encounter.full._single_coding_kwargs's docstring for
    the full reasoning (and the TypeError that first caught this)."""
    return {
        k: v
        for k, v in {
            "system": obj.system,
            "version": obj.version,
            "code": obj.code,
            "display": obj.display,
            "userSelected": obj.user_selected,
        }.items()
        if v is not None
    }


def _fhir_coding_list(codings) -> list[dict]:
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


def fhir_encounter_identifier(i) -> dict:
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


def fhir_encounter_status_history(sh) -> dict:
    entry: dict = {}
    status = fhir_enum(sh.status)
    if status:
        entry["status"] = status.replace("_", "-") if status else status
    period = _fhir_period(sh.period_start, sh.period_end)
    if period:
        entry["period"] = period
    return entry


def fhir_encounter_class_history(ch) -> dict:
    entry: dict = {}
    coding = _fhir_single_coding(ch)
    if coding:
        entry["class"] = coding
    period = _fhir_period(ch.period_start, ch.period_end)
    if period:
        entry["period"] = period
    return entry


def fhir_encounter_type(t) -> dict:
    return _fhir_cc(t.codings, t.text)


def fhir_encounter_reason_code(rc) -> dict:
    return _fhir_cc(rc.codings, rc.text)


def fhir_encounter_episode_of_care(eoc) -> dict:
    return _fhir_reference(eoc, "reference")


def fhir_encounter_based_on(bo) -> dict:
    return _fhir_reference(bo, "reference")


def fhir_encounter_appointment(ap) -> dict:
    return _fhir_reference(ap, "reference")


def fhir_encounter_reason_reference(rr) -> dict:
    return _fhir_reference(rr, "reference")


def fhir_encounter_account(ac) -> dict:
    return _fhir_reference(ac, "reference")


def fhir_encounter_participant_type(pt) -> dict:
    return _fhir_cc(pt.codings, pt.text)


def fhir_encounter_participant(p) -> dict:
    entry: dict = {}
    types = [fhir_encounter_participant_type(t) for t in (p.types or [])]
    types = [t for t in types if t]
    if types:
        entry["type"] = types
    period = _fhir_period(p.period_start, p.period_end)
    if period:
        entry["period"] = period
    individual = _fhir_reference(p, "individual")
    if individual:
        entry["individual"] = individual
    return entry


def fhir_encounter_diagnosis(d) -> dict:
    entry: dict = {}
    condition = _fhir_reference(d, "condition")
    if condition:
        entry["condition"] = condition
    use = _fhir_cc(d.use_codings, d.use_text)
    if use:
        entry["use"] = use
    if d.rank is not None:
        entry["rank"] = d.rank
    return entry


def fhir_encounter_hospitalization(h) -> dict:
    entry: dict = {}

    pre_admission_identifier: dict = {}
    if h.pre_admission_identifier_use:
        pre_admission_identifier["use"] = fhir_enum(h.pre_admission_identifier_use)
    type_cc = _fhir_cc(h.pre_admission_identifier_type_codings, h.pre_admission_identifier_type_text)
    if type_cc:
        pre_admission_identifier["type"] = type_cc
    if h.pre_admission_identifier_system:
        pre_admission_identifier["system"] = h.pre_admission_identifier_system
    if h.pre_admission_identifier_value:
        pre_admission_identifier["value"] = h.pre_admission_identifier_value
    period = _fhir_period(h.pre_admission_identifier_period_start, h.pre_admission_identifier_period_end)
    if period:
        pre_admission_identifier["period"] = period
    assigner = _fhir_reference(h, "pre_admission_identifier_assigner")
    if assigner:
        pre_admission_identifier["assigner"] = assigner
    if pre_admission_identifier:
        entry["preAdmissionIdentifier"] = pre_admission_identifier

    origin = _fhir_reference(h, "origin")
    if origin:
        entry["origin"] = origin

    admit_source = _fhir_cc(h.admit_source_codings, h.admit_source_text)
    if admit_source:
        entry["admitSource"] = admit_source

    re_admission = _fhir_cc(h.re_admission_codings, h.re_admission_text)
    if re_admission:
        entry["reAdmission"] = re_admission

    diet_preferences = [_fhir_cc(dp.codings, dp.text) for dp in (h.diet_preferences or [])]
    diet_preferences = [dp for dp in diet_preferences if dp]
    if diet_preferences:
        entry["dietPreference"] = diet_preferences

    special_courtesies = [_fhir_cc(sc.codings, sc.text) for sc in (h.special_courtesies or [])]
    special_courtesies = [sc for sc in special_courtesies if sc]
    if special_courtesies:
        entry["specialCourtesy"] = special_courtesies

    special_arrangements = [_fhir_cc(sa.codings, sa.text) for sa in (h.special_arrangements or [])]
    special_arrangements = [sa for sa in special_arrangements if sa]
    if special_arrangements:
        entry["specialArrangement"] = special_arrangements

    destination = _fhir_reference(h, "destination")
    if destination:
        entry["destination"] = destination

    discharge_disposition = _fhir_cc(h.discharge_disposition_codings, h.discharge_disposition_text)
    if discharge_disposition:
        entry["dischargeDisposition"] = discharge_disposition

    return entry


def fhir_encounter_location(loc) -> dict:
    entry: dict = {}
    location = _fhir_reference(loc, "location")
    if location:
        entry["location"] = location
    status = fhir_enum(loc.status)
    if status:
        entry["status"] = status
    physical_type = _fhir_cc(loc.physical_type_codings, loc.physical_type_text)
    if physical_type:
        entry["physicalType"] = physical_type
    period = _fhir_period(loc.period_start, loc.period_end)
    if period:
        entry["period"] = period
    return entry


# Base URL for this server's own, not-yet-formally-registered extensions —
# same convention as app.fhir.mappers.organization.fhir._EXT_BASE.
_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(encounter: EncounterModel) -> dict:
    meta: dict = {}
    if encounter.updated_at:
        meta["lastUpdated"] = fhir_instant(encounter.updated_at)

    extensions = []
    if encounter.tenant_id:
        extensions.append({"url": f"{_EXT_BASE}/org-id", "valueString": encounter.tenant_id})
    if encounter.created_by:
        extensions.append({"url": f"{_EXT_BASE}/created-by", "valueString": encounter.created_by})
    if encounter.updated_by:
        extensions.append({"url": f"{_EXT_BASE}/updated-by", "valueString": encounter.updated_by})
    if encounter.created_at:
        extensions.append(
            {"url": f"{_EXT_BASE}/created-at", "valueDateTime": fhir_instant(encounter.created_at)}
        )
    if extensions:
        meta["extension"] = extensions

    return meta


def to_fhir_encounter(encounter: EncounterModel) -> dict:
    result: dict = {
        "resourceType": "Encounter",
        "id": str(encounter.encounter_id),
    }

    meta = _fhir_meta(encounter)
    if meta:
        result["meta"] = meta

    if encounter.extension:
        result["extension"] = list(encounter.extension)

    identifiers = [fhir_encounter_identifier(i) for i in (encounter.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    status = fhir_enum(encounter.status)
    if status:
        result["status"] = status.replace("_", "-")

    class_coding = _fhir_single_coding(encounter)
    if class_coding:
        result["class"] = class_coding

    types = [fhir_encounter_type(t) for t in (encounter.types or [])]
    types = [t for t in types if t]
    if types:
        result["type"] = types

    service_type = _fhir_cc(encounter.service_type_codings, encounter.service_type_text)
    if service_type:
        result["serviceType"] = service_type

    priority = _fhir_cc(encounter.priority_codings, encounter.priority_text)
    if priority:
        result["priority"] = priority

    subject = _fhir_reference(encounter, "subject")
    if subject:
        result["subject"] = subject

    episode_of_cares = [fhir_encounter_episode_of_care(eoc) for eoc in (encounter.episode_of_cares or [])]
    episode_of_cares = [eoc for eoc in episode_of_cares if eoc]
    if episode_of_cares:
        result["episodeOfCare"] = episode_of_cares

    based_ons = [fhir_encounter_based_on(bo) for bo in (encounter.based_ons or [])]
    based_ons = [bo for bo in based_ons if bo]
    if based_ons:
        result["basedOn"] = based_ons

    participants = [fhir_encounter_participant(p) for p in (encounter.participants or [])]
    participants = [p for p in participants if p]
    if participants:
        result["participant"] = participants

    appointments = [fhir_encounter_appointment(a) for a in (encounter.appointments or [])]
    appointments = [a for a in appointments if a]
    if appointments:
        result["appointment"] = appointments

    period = _fhir_period(encounter.period_start, encounter.period_end)
    if period:
        result["period"] = period

    length: dict = {}
    if encounter.length_value is not None:
        length["value"] = float(encounter.length_value)
    if encounter.length_comparator:
        comparator = fhir_enum(encounter.length_comparator)
        length["comparator"] = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}.get(comparator, comparator)
    if encounter.length_unit:
        length["unit"] = encounter.length_unit
    if encounter.length_system:
        length["system"] = encounter.length_system
    if encounter.length_code:
        length["code"] = encounter.length_code
    if length:
        result["length"] = length

    reason_codes = [fhir_encounter_reason_code(rc) for rc in (encounter.reason_codes or [])]
    reason_codes = [rc for rc in reason_codes if rc]
    if reason_codes:
        result["reasonCode"] = reason_codes

    reason_references = [fhir_encounter_reason_reference(rr) for rr in (encounter.reason_references or [])]
    reason_references = [rr for rr in reason_references if rr]
    if reason_references:
        result["reasonReference"] = reason_references

    diagnoses = [fhir_encounter_diagnosis(d) for d in (encounter.diagnoses or [])]
    diagnoses = [d for d in diagnoses if d]
    if diagnoses:
        result["diagnosis"] = diagnoses

    accounts = [fhir_encounter_account(a) for a in (encounter.accounts or [])]
    accounts = [a for a in accounts if a]
    if accounts:
        result["account"] = accounts

    if encounter.hospitalization:
        hospitalization = fhir_encounter_hospitalization(encounter.hospitalization)
        if hospitalization:
            result["hospitalization"] = hospitalization

    locations = [fhir_encounter_location(loc) for loc in (encounter.locations or [])]
    locations = [loc for loc in locations if loc]
    if locations:
        result["location"] = locations

    service_provider = _fhir_reference(encounter, "service_provider")
    if service_provider:
        result["serviceProvider"] = service_provider

    part_of = _fhir_reference(encounter, "part_of")
    if part_of:
        result["partOf"] = part_of

    status_history = [fhir_encounter_status_history(sh) for sh in (encounter.status_history or [])]
    status_history = [sh for sh in status_history if sh]
    if status_history:
        result["statusHistory"] = status_history

    class_history = [fhir_encounter_class_history(ch) for ch in (encounter.class_history or [])]
    class_history = [ch for ch in class_history if ch]
    if class_history:
        result["classHistory"] = class_history

    return {k: v for k, v in result.items() if v is not None}
