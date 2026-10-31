"""Payload -> FHIR JSON conversion for AllergyIntolerance.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(AllergyIntoleranceCreateSchema / AllergyIntolerancePatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant, merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.allergy_intolerance.input import (
        AllergyIntoleranceCodeableConceptInput,
        AllergyIntoleranceCreateSchema,
        AllergyIntoleranceIdentifierInput,
        AllergyIntoleranceNoteInput,
        AllergyIntolerancePatchSchema,
        AllergyIntoleranceReactionInput,
    )

_PATIENT_FIELDS = {"patient", "patient_display"}
_ENCOUNTER_FIELDS = {"encounter", "encounter_display"}
_RECORDER_FIELDS = {"recorder", "recorder_display"}
_ASSERTER_FIELDS = {"asserter", "asserter_display"}
_ONSET_PERIOD_FIELDS = {"onset_period_start", "onset_period_end"}


def _coding_from_payload(c: Any) -> dict:
    if isinstance(c, dict):
        return {
            k: v
            for k, v in {
                "system": c.get("system"),
                "version": c.get("version"),
                "code": c.get("code"),
                "display": c.get("display"),
                "userSelected": c.get("user_selected") or c.get("userSelected"),
            }.items()
            if v is not None
        }
    return {
        k: v
        for k, v in {
            "system": getattr(c, "system", None),
            "version": getattr(c, "version", None),
            "code": getattr(c, "code", None),
            "display": getattr(c, "display", None),
            "userSelected": getattr(c, "user_selected", None),
        }.items()
        if v is not None
    }


def _codeable_concept_from_payload(
    concept: AllergyIntoleranceCodeableConceptInput | dict | None,
) -> dict | None:
    if not concept:
        return None
    if isinstance(concept, dict):
        codings = [_coding_from_payload(c) for c in (concept.get("coding") or [])]
        codings = [c for c in codings if c]
        text = concept.get("text")
    else:
        codings = [_coding_from_payload(c) for c in (concept.coding or [])]
        codings = [c for c in codings if c]
        text = concept.text

    result: dict = {}
    if codings:
        result["coding"] = codings
    if text:
        result["text"] = text
    return result or None


def _identifier_from_payload(
    ident: AllergyIntoleranceIdentifierInput | dict | None,
) -> dict | None:
    if not ident:
        return None
    entry: dict = {}
    if isinstance(ident, dict):
        use = ident.get("use")
        type_in = ident.get("type")
        system = ident.get("system")
        value = ident.get("value")
        p_start = ident.get("period_start")
        p_end = ident.get("period_end")
        assigner = ident.get("assigner")
        assigner_disp = ident.get("assigner_display")
    else:
        use = ident.use
        type_in = ident.type
        system = ident.system
        value = ident.value
        p_start = ident.period_start
        p_end = ident.period_end
        assigner = ident.assigner
        assigner_disp = ident.assigner_display

    if use:
        entry["use"] = fhir_enum(use)
    type_cc = _codeable_concept_from_payload(type_in)
    if type_cc:
        entry["type"] = type_cc
    if system:
        entry["system"] = system
    if value:
        entry["value"] = value
    if p_start or p_end:
        period: dict = {}
        if p_start:
            period["start"] = fhir_instant(p_start)
        if p_end:
            period["end"] = fhir_instant(p_end)
        entry["period"] = period
    if assigner:
        ref_obj: dict = {"reference": assigner}
        if assigner_disp:
            ref_obj["display"] = assigner_disp
        entry["assigner"] = ref_obj

    return entry or None


def _annotation_from_payload(
    note: AllergyIntoleranceNoteInput | dict | None,
) -> dict | None:
    if not note:
        return None
    if isinstance(note, dict):
        text = note.get("text")
        time_val = note.get("time")
        author_str = note.get("author_string")
        author_ref_str = note.get("author_reference")
        author_ref_disp = note.get("author_reference_display")
    else:
        text = note.text
        time_val = note.time
        author_str = note.author_string
        author_ref_str = note.author_reference
        author_ref_disp = note.author_reference_display

    entry: dict = {}
    if text:
        entry["text"] = text
    if time_val:
        entry["time"] = fhir_instant(time_val)
    if author_ref_str:
        ref: dict = {"reference": author_ref_str}
        if author_ref_disp:
            ref["display"] = author_ref_disp
        entry["authorReference"] = ref
    elif author_str:
        entry["authorString"] = author_str
    return entry or None


def _reaction_from_payload(
    r: AllergyIntoleranceReactionInput | dict | None,
) -> dict | None:
    if not r:
        return None
    if isinstance(r, dict):
        substance = r.get("substance")
        manifestation = r.get("manifestation") or []
        description = r.get("description")
        onset = r.get("onset")
        severity = r.get("severity")
        exposure_route = r.get("exposure_route")
        notes = r.get("note") or []
    else:
        substance = r.substance
        manifestation = r.manifestation or []
        description = r.description
        onset = r.onset
        severity = r.severity
        exposure_route = r.exposure_route
        notes = r.note or []

    entry: dict = {}
    substance_cc = _codeable_concept_from_payload(substance)
    if substance_cc:
        entry["substance"] = substance_cc

    manif_list = [
        m for m in [_codeable_concept_from_payload(x) for x in manifestation] if m
    ]
    if manif_list:
        entry["manifestation"] = manif_list

    if description:
        entry["description"] = description
    if onset:
        entry["onset"] = fhir_instant(onset)
    if severity:
        entry["severity"] = fhir_enum(severity)

    exposure_cc = _codeable_concept_from_payload(exposure_route)
    if exposure_cc:
        entry["exposureRoute"] = exposure_cc

    note_list = [n for n in [_annotation_from_payload(x) for x in notes] if n]
    if note_list:
        entry["note"] = note_list

    return entry or None


def payload_to_fhir_allergy_intolerance(
    payload: AllergyIntoleranceCreateSchema,
) -> dict:
    """Convert AllergyIntoleranceCreateSchema to a FHIR-compliant resource dict."""
    res: dict[str, Any] = {
        "resourceType": "AllergyIntolerance",
    }

    if payload.identifier:
        id_list = [_identifier_from_payload(i) for i in payload.identifier]
        id_list = [i for i in id_list if i]
        if id_list:
            res["identifier"] = id_list

    clin_status = _codeable_concept_from_payload(payload.clinical_status)
    if clin_status:
        res["clinicalStatus"] = clin_status

    ver_status = _codeable_concept_from_payload(payload.verification_status)
    if ver_status:
        res["verificationStatus"] = ver_status

    if payload.type:
        res["type"] = fhir_enum(payload.type)

    if payload.category:
        cat_list = [fhir_enum(c) for c in payload.category]
        if cat_list:
            res["category"] = cat_list

    if payload.criticality:
        res["criticality"] = fhir_enum(payload.criticality)

    code_cc = _codeable_concept_from_payload(payload.code)
    if code_cc:
        res["code"] = code_cc

    # patient (1..1)
    patient_ref: dict = {"reference": payload.patient}
    if payload.patient_display:
        patient_ref["display"] = payload.patient_display
    res["patient"] = patient_ref

    if payload.encounter:
        encounter_ref: dict = {"reference": payload.encounter}
        if payload.encounter_display:
            encounter_ref["display"] = payload.encounter_display
        res["encounter"] = encounter_ref

    # Choice onset[x]
    if payload.onset_date_time:
        res["onsetDateTime"] = fhir_instant(payload.onset_date_time)
    elif payload.onset_age:
        res["onsetAge"] = payload.onset_age
    elif payload.onset_period_start or payload.onset_period_end:
        period: dict = {}
        if payload.onset_period_start:
            period["start"] = fhir_instant(payload.onset_period_start)
        if payload.onset_period_end:
            period["end"] = fhir_instant(payload.onset_period_end)
        res["onsetPeriod"] = period
    elif payload.onset_range:
        res["onsetRange"] = payload.onset_range
    elif payload.onset_string:
        res["onsetString"] = payload.onset_string

    if payload.recorded_date:
        res["recordedDate"] = fhir_instant(payload.recorded_date)

    if payload.recorder:
        rec_ref: dict = {"reference": payload.recorder}
        if payload.recorder_display:
            rec_ref["display"] = payload.recorder_display
        res["recorder"] = rec_ref

    if payload.asserter:
        ass_ref: dict = {"reference": payload.asserter}
        if payload.asserter_display:
            ass_ref["display"] = payload.asserter_display
        res["asserter"] = ass_ref

    if payload.last_occurrence:
        res["lastOccurrence"] = fhir_instant(payload.last_occurrence)

    if payload.note:
        note_list = [_annotation_from_payload(n) for n in payload.note]
        note_list = [n for n in note_list if n]
        if note_list:
            res["note"] = note_list

    if payload.reaction:
        rx_list = [_reaction_from_payload(r) for r in payload.reaction]
        rx_list = [r for r in rx_list if r]
        if rx_list:
            res["reaction"] = rx_list

    if payload.extension:
        res["extension"] = payload.extension

    return {k: v for k, v in res.items() if v is not None}


def patch_fragment_to_fhir_allergy_intolerance(
    payload: AllergyIntolerancePatchSchema,
) -> tuple[dict[str, Any], set[str]]:
    """Convert AllergyIntolerancePatchSchema to a partial FHIR fragment and set of touched fields."""
    fragment: dict[str, Any] = {}
    touched: set[str] = set()
    fields_set = payload.model_fields_set

    if "clinical_status" in fields_set:
        touched.add("clinicalStatus")
        if payload.clinical_status is not None:
            fragment["clinicalStatus"] = _codeable_concept_from_payload(
                payload.clinical_status
            )

    if "verification_status" in fields_set:
        touched.add("verificationStatus")
        if payload.verification_status is not None:
            fragment["verificationStatus"] = _codeable_concept_from_payload(
                payload.verification_status
            )

    if "type" in fields_set:
        touched.add("type")
        if payload.type is not None:
            fragment["type"] = fhir_enum(payload.type)

    if "category" in fields_set:
        touched.add("category")
        if payload.category is not None:
            fragment["category"] = [fhir_enum(c) for c in payload.category]

    if "criticality" in fields_set:
        touched.add("criticality")
        if payload.criticality is not None:
            fragment["criticality"] = fhir_enum(payload.criticality)

    if "code" in fields_set:
        touched.add("code")
        if payload.code is not None:
            fragment["code"] = _codeable_concept_from_payload(payload.code)

    if _PATIENT_FIELDS & fields_set:
        touched.add("patient")
        if payload.patient is not None or payload.patient_display is not None:
            ref: dict = {}
            if payload.patient:
                ref["reference"] = payload.patient
            if payload.patient_display:
                ref["display"] = payload.patient_display
            if ref:
                fragment["patient"] = ref

    if _ENCOUNTER_FIELDS & fields_set:
        touched.add("encounter")
        if payload.encounter is not None or payload.encounter_display is not None:
            ref: dict = {}
            if payload.encounter:
                ref["reference"] = payload.encounter
            if payload.encounter_display:
                ref["display"] = payload.encounter_display
            if ref:
                fragment["encounter"] = ref

    if "onset_date_time" in fields_set:
        touched.add("onsetDateTime")
        if payload.onset_date_time is not None:
            fragment["onsetDateTime"] = fhir_instant(payload.onset_date_time)

    if "onset_age" in fields_set:
        touched.add("onsetAge")
        if payload.onset_age is not None:
            fragment["onsetAge"] = payload.onset_age

    if _ONSET_PERIOD_FIELDS & fields_set:
        touched.add("onsetPeriod")
        period: dict = {}
        if payload.onset_period_start is not None:
            period["start"] = fhir_instant(payload.onset_period_start)
        if payload.onset_period_end is not None:
            period["end"] = fhir_instant(payload.onset_period_end)
        if period:
            fragment["onsetPeriod"] = period

    if "onset_range" in fields_set:
        touched.add("onsetRange")
        if payload.onset_range is not None:
            fragment["onsetRange"] = payload.onset_range

    if "onset_string" in fields_set:
        touched.add("onsetString")
        if payload.onset_string is not None:
            fragment["onsetString"] = payload.onset_string

    if "recorded_date" in fields_set:
        touched.add("recordedDate")
        if payload.recorded_date is not None:
            fragment["recordedDate"] = fhir_instant(payload.recorded_date)

    if _RECORDER_FIELDS & fields_set:
        touched.add("recorder")
        if payload.recorder is not None or payload.recorder_display is not None:
            ref = {}
            if payload.recorder:
                ref["reference"] = payload.recorder
            if payload.recorder_display:
                ref["display"] = payload.recorder_display
            if ref:
                fragment["recorder"] = ref

    if _ASSERTER_FIELDS & fields_set:
        touched.add("asserter")
        if payload.asserter is not None or payload.asserter_display is not None:
            ref = {}
            if payload.asserter:
                ref["reference"] = payload.asserter
            if payload.asserter_display:
                ref["display"] = payload.asserter_display
            if ref:
                fragment["asserter"] = ref

    if "last_occurrence" in fields_set:
        touched.add("lastOccurrence")
        if payload.last_occurrence is not None:
            fragment["lastOccurrence"] = fhir_instant(payload.last_occurrence)

    if "note" in fields_set:
        touched.add("note")
        if payload.note is not None:
            fragment["note"] = [
                n for n in [_annotation_from_payload(x) for x in payload.note] if n
            ]

    if "reaction" in fields_set:
        touched.add("reaction")
        if payload.reaction is not None:
            fragment["reaction"] = [
                r for r in [_reaction_from_payload(x) for x in payload.reaction] if r
            ]

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                i
                for i in [_identifier_from_payload(x) for x in payload.identifier]
                if i
            ]

    if "extension" in fields_set:
        touched.add("extension")
        if payload.extension is not None:
            fragment["extension"] = payload.extension

    return fragment, touched
