"""Payload -> FHIR JSON conversion, the mirror image of fhir.py. See
app.fhir.mappers.appointment.payload's module docstring for the full
reasoning — this mirrors it exactly for Encounter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.encounter import EncounterCreateSchema, EncounterPatchSchema


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


def _single_coding(c) -> dict:
    """A single CodingInput object (not a list) -> a bare FHIR Coding
    dict — used for Encounter.class / Encounter.classHistory.class."""
    if c is None:
        return {}
    return {
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


def payload_status_history(sh) -> dict:
    entry: dict = {}
    if sh.status:
        entry["status"] = sh.status.value
    period = _period(sh.period_start, sh.period_end)
    if period:
        entry["period"] = period
    return entry


def payload_class_history(ch) -> dict:
    entry: dict = {}
    coding = _single_coding(ch.class_coding)
    if coding:
        entry["class"] = coding
    period = _period(ch.period_start, ch.period_end)
    if period:
        entry["period"] = period
    return entry


def payload_type(t) -> dict:
    return _cc(t.coding, t.text)


def payload_reason_code(rc) -> dict:
    return _cc(rc.coding, rc.text)


def payload_episode_of_care(eoc) -> dict:
    return _reference_from_payload(eoc, "reference")


def payload_based_on(bo) -> dict:
    return _reference_from_payload(bo, "reference")


def payload_appointment(ap) -> dict:
    return _reference_from_payload(ap, "reference")


def payload_reason_reference(rr) -> dict:
    return _reference_from_payload(rr, "reference")


def payload_account(ac) -> dict:
    return _reference_from_payload(ac, "reference")


def payload_participant_type(pt) -> dict:
    return _cc(pt.coding, pt.text)


def payload_participant(p) -> dict:
    entry: dict = {}
    types = [payload_participant_type(t) for t in (p.type or [])]
    types = [t for t in types if t]
    if types:
        entry["type"] = types
    period = _period(p.period_start, p.period_end)
    if period:
        entry["period"] = period
    individual = _reference_from_payload(p, "individual")
    if individual:
        entry["individual"] = individual
    return entry


def payload_diagnosis(d) -> dict:
    entry: dict = {}
    condition = _reference_from_payload(d, "condition")
    if condition:
        entry["condition"] = condition
    use = _cc(d.use_coding, d.use_text)
    if use:
        entry["use"] = use
    if d.rank is not None:
        entry["rank"] = d.rank
    return entry


def payload_hospitalization(h) -> dict:
    entry: dict = {}

    pre_admission_identifier: dict = {}
    if h.pre_admission_identifier_use:
        pre_admission_identifier["use"] = fhir_enum(h.pre_admission_identifier_use)
    type_cc = _cc(h.pre_admission_identifier_type_coding, h.pre_admission_identifier_type_text)
    if type_cc:
        pre_admission_identifier["type"] = type_cc
    if h.pre_admission_identifier_system:
        pre_admission_identifier["system"] = h.pre_admission_identifier_system
    if h.pre_admission_identifier_value:
        pre_admission_identifier["value"] = h.pre_admission_identifier_value
    period = _period(h.pre_admission_identifier_period_start, h.pre_admission_identifier_period_end)
    if period:
        pre_admission_identifier["period"] = period
    assigner = _reference_from_payload(h, "pre_admission_identifier_assigner")
    if assigner:
        pre_admission_identifier["assigner"] = assigner
    if pre_admission_identifier:
        entry["preAdmissionIdentifier"] = pre_admission_identifier

    origin = _reference_from_payload(h, "origin")
    if origin:
        entry["origin"] = origin

    admit_source = _cc(h.admit_source_coding, h.admit_source_text)
    if admit_source:
        entry["admitSource"] = admit_source

    re_admission = _cc(h.re_admission_coding, h.re_admission_text)
    if re_admission:
        entry["reAdmission"] = re_admission

    diet_preferences = [_cc(dp.coding, dp.text) for dp in (h.diet_preference or [])]
    diet_preferences = [dp for dp in diet_preferences if dp]
    if diet_preferences:
        entry["dietPreference"] = diet_preferences

    special_courtesies = [_cc(sc.coding, sc.text) for sc in (h.special_courtesy or [])]
    special_courtesies = [sc for sc in special_courtesies if sc]
    if special_courtesies:
        entry["specialCourtesy"] = special_courtesies

    special_arrangements = [_cc(sa.coding, sa.text) for sa in (h.special_arrangement or [])]
    special_arrangements = [sa for sa in special_arrangements if sa]
    if special_arrangements:
        entry["specialArrangement"] = special_arrangements

    destination = _reference_from_payload(h, "destination")
    if destination:
        entry["destination"] = destination

    discharge_disposition = _cc(h.discharge_disposition_coding, h.discharge_disposition_text)
    if discharge_disposition:
        entry["dischargeDisposition"] = discharge_disposition

    return entry


def payload_location(loc) -> dict:
    entry: dict = {}
    location = _reference_from_payload(loc, "location")
    if location:
        entry["location"] = location
    if loc.status:
        entry["status"] = loc.status.value
    physical_type = _cc(loc.physical_type_coding, loc.physical_type_text)
    if physical_type:
        entry["physicalType"] = physical_type
    period = _period(loc.period_start, loc.period_end)
    if period:
        entry["period"] = period
    return entry


def payload_status(status) -> str | None:
    """Status is the one field this module intentionally does NOT route
    through fhir_enum() — the input schema's app.schemas.enums.EncounterStatus
    already carries the true hyphenated FHIR code as its .value."""
    return status.value if status else None


# Every Encounter field that's a 0..* list, mapped to the builder that
# renders one of its items, and to the FHIR camelCase key it lands under —
# shared by both orchestrators below.
_LIST_FIELDS = {
    "identifier": ("identifier", payload_identifier),
    "status_history": ("statusHistory", payload_status_history),
    "class_history": ("classHistory", payload_class_history),
    "type": ("type", payload_type),
    "episode_of_care": ("episodeOfCare", payload_episode_of_care),
    "based_on": ("basedOn", payload_based_on),
    "appointment": ("appointment", payload_appointment),
    "reason_code": ("reasonCode", payload_reason_code),
    "reason_reference": ("reasonReference", payload_reason_reference),
    "account": ("account", payload_account),
    "participant": ("participant", payload_participant),
    "diagnosis": ("diagnosis", payload_diagnosis),
    "location": ("location", payload_location),
}

_SUBJECT_FIELDS = {
    "subject", "subject_display", "subject_identifier_use", "subject_identifier_type_system",
    "subject_identifier_type_version", "subject_identifier_type_code", "subject_identifier_type_display",
    "subject_identifier_type_text", "subject_identifier_type_user_selected", "subject_identifier_system",
    "subject_identifier_value", "subject_identifier_period_start", "subject_identifier_period_end",
}
_SERVICE_PROVIDER_FIELDS = {
    "service_provider", "service_provider_display", "service_provider_identifier_use",
    "service_provider_identifier_type_system", "service_provider_identifier_type_version",
    "service_provider_identifier_type_code", "service_provider_identifier_type_display",
    "service_provider_identifier_type_text", "service_provider_identifier_type_user_selected",
    "service_provider_identifier_system", "service_provider_identifier_value",
    "service_provider_identifier_period_start", "service_provider_identifier_period_end",
}
_PART_OF_FIELDS = {
    "part_of", "part_of_display", "part_of_identifier_use", "part_of_identifier_type_system",
    "part_of_identifier_type_version", "part_of_identifier_type_code", "part_of_identifier_type_display",
    "part_of_identifier_type_text", "part_of_identifier_type_user_selected", "part_of_identifier_system",
    "part_of_identifier_value", "part_of_identifier_period_start", "part_of_identifier_period_end",
}
_LENGTH_FIELDS = {"length_value", "length_comparator", "length_unit", "length_system", "length_code"}


def payload_to_fhir_encounter(payload: EncounterCreateSchema) -> dict:
    """Full-resource conversion for CREATE: a create payload represents
    the resource's entire initial state, so every field is considered
    present — unlike patch_fragment_to_fhir_encounter()'s tri-state
    handling."""
    result: dict = {"resourceType": "Encounter"}

    if payload.extension:
        result["extension"] = list(payload.extension)
    status = payload_status(payload.status)
    if status:
        result["status"] = status
    class_coding = _single_coding(payload.class_coding)
    if class_coding:
        result["class"] = class_coding
    service_type = _cc(payload.service_type_coding, payload.service_type_text)
    if service_type:
        result["serviceType"] = service_type
    priority = _cc(payload.priority_coding, payload.priority_text)
    if priority:
        result["priority"] = priority
    subject = _reference_from_payload(payload, "subject")
    if subject:
        result["subject"] = subject
    period = _period(payload.period_start, payload.period_end)
    if period:
        result["period"] = period
    length: dict = {}
    if payload.length_value is not None:
        length["value"] = float(payload.length_value)
    if payload.length_comparator:
        length["comparator"] = payload.length_comparator.value
    if payload.length_unit:
        length["unit"] = payload.length_unit
    if payload.length_system:
        length["system"] = payload.length_system
    if payload.length_code:
        length["code"] = payload.length_code
    if length:
        result["length"] = length
    service_provider = _reference_from_payload(payload, "service_provider")
    if service_provider:
        result["serviceProvider"] = service_provider
    part_of = _reference_from_payload(payload, "part_of")
    if part_of:
        result["partOf"] = part_of
    if payload.hospitalization:
        hospitalization = payload_hospitalization(payload.hospitalization)
        if hospitalization:
            result["hospitalization"] = hospitalization

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        items = [item for item in items if item]
        if items:
            result[fhir_key] = items

    return result


def patch_fragment_to_fhir_encounter(payload: EncounterPatchSchema) -> tuple[dict, set[str]]:
    """Converts only the fields a PATCH request actually supplied (per
    `model_fields_set`) into a FHIR-shaped fragment, alongside the set of
    top-level FHIR keys the request touched."""
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
    if "class_coding" in provided:
        touched.add("class")
        coding = _single_coding(payload.class_coding)
        if coding:
            fragment["class"] = coding
    if provided & {"service_type_coding", "service_type_text"}:
        touched.add("serviceType")
        service_type = _cc(payload.service_type_coding, payload.service_type_text)
        if service_type:
            fragment["serviceType"] = service_type
    if provided & {"priority_coding", "priority_text"}:
        touched.add("priority")
        priority = _cc(payload.priority_coding, payload.priority_text)
        if priority:
            fragment["priority"] = priority
    if provided & _SUBJECT_FIELDS:
        touched.add("subject")
        subject = _reference_from_payload(payload, "subject")
        if subject:
            fragment["subject"] = subject
    if "period_start" in provided or "period_end" in provided:
        touched.add("period")
        period = _period(payload.period_start, payload.period_end)
        if period:
            fragment["period"] = period
    if provided & _LENGTH_FIELDS:
        touched.add("length")
        length: dict = {}
        if payload.length_value is not None:
            length["value"] = float(payload.length_value)
        if payload.length_comparator:
            length["comparator"] = payload.length_comparator.value
        if payload.length_unit:
            length["unit"] = payload.length_unit
        if payload.length_system:
            length["system"] = payload.length_system
        if payload.length_code:
            length["code"] = payload.length_code
        if length:
            fragment["length"] = length
    if provided & _SERVICE_PROVIDER_FIELDS:
        touched.add("serviceProvider")
        service_provider = _reference_from_payload(payload, "service_provider")
        if service_provider:
            fragment["serviceProvider"] = service_provider
    if provided & _PART_OF_FIELDS:
        touched.add("partOf")
        part_of = _reference_from_payload(payload, "part_of")
        if part_of:
            fragment["partOf"] = part_of
    if "hospitalization" in provided:
        touched.add("hospitalization")
        if payload.hospitalization:
            hospitalization = payload_hospitalization(payload.hospitalization)
            if hospitalization:
                fragment["hospitalization"] = hospitalization

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            items = [builder(item) for item in (getattr(payload, field, None) or [])]
            items = [item for item in items if item]
            if items:
                fragment[fhir_key] = items

    return fragment, touched
