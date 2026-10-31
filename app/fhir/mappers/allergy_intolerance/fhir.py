from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.allergy_intolerance import (
        AllergyIntoleranceIdentifier,
        AllergyIntoleranceModel,
        AllergyIntoleranceNote,
        AllergyIntoleranceReaction,
        AllergyIntoleranceReactionNote,
    )


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


def _fhir_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_ref(
    ref_raw: str | None,
    ref_type: Any,
    ref_id: int | None,
    display: str | None,
) -> dict | None:
    result: dict = {}
    if ref_raw:
        result["reference"] = ref_raw
    elif ref_type and ref_id:
        result["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        result["display"] = display
    return result or None


def _fhir_identifier(i: AllergyIntoleranceIdentifier) -> dict | None:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = _fhir_codeable_concept(getattr(i, "type_codings", None), i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        period: dict = {}
        if i.period_start:
            period["start"] = fhir_instant(i.period_start)
        if i.period_end:
            period["end"] = fhir_instant(i.period_end)
        entry["period"] = period
    assigner = _fhir_ref(
        i.assigner_reference,
        i.assigner_type,
        i.assigner_id,
        i.assigner_display,
    )
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_annotation(
    note: AllergyIntoleranceNote | AllergyIntoleranceReactionNote,
) -> dict | None:
    entry: dict = {}
    author_ref = _fhir_ref(
        None,
        getattr(note, "author_reference_type", None),
        getattr(note, "author_reference_id", None),
        getattr(note, "author_reference_display", None),
    )
    if author_ref:
        entry["authorReference"] = author_ref
    elif getattr(note, "author_string", None):
        entry["authorString"] = note.author_string
    if getattr(note, "time", None):
        entry["time"] = fhir_instant(note.time)
    if getattr(note, "text", None):
        entry["text"] = note.text
    return entry or None


def _fhir_reaction(r: AllergyIntoleranceReaction) -> dict | None:
    entry: dict = {}
    substance_cc = _fhir_codeable_concept(
        getattr(r, "substance_codings", None), getattr(r, "substance_text", None)
    )
    if substance_cc:
        entry["substance"] = substance_cc

    manifestation_list = []
    for m in getattr(r, "manifestations", None) or []:
        m_cc = _fhir_codeable_concept(
            getattr(m, "codings", None), getattr(m, "text", None)
        )
        if m_cc:
            manifestation_list.append(m_cc)
    if manifestation_list:
        entry["manifestation"] = manifestation_list

    if getattr(r, "description", None):
        entry["description"] = r.description
    if getattr(r, "onset", None):
        entry["onset"] = fhir_instant(r.onset)
    if getattr(r, "severity", None):
        entry["severity"] = fhir_enum(r.severity)

    exposure_route_cc = _fhir_codeable_concept(
        getattr(r, "exposure_route_codings", None),
        getattr(r, "exposure_route_text", None),
    )
    if exposure_route_cc:
        entry["exposureRoute"] = exposure_route_cc

    if getattr(r, "notes", None):
        note_list = [_fhir_annotation(n) for n in r.notes]
        note_list = [n for n in note_list if n]
        if note_list:
            entry["note"] = note_list

    return entry or None


def to_fhir_allergy_intolerance(model: AllergyIntoleranceModel) -> dict:
    """Map AllergyIntoleranceModel ORM instance to FHIR R4 AllergyIntolerance resource dict."""
    res: dict[str, Any] = {
        "resourceType": "AllergyIntolerance",
        "id": str(model.allergy_intolerance_id),
    }

    if model.updated_at:
        res["meta"] = {
            "versionId": "1",
            "lastUpdated": fhir_instant(model.updated_at),
        }

    if getattr(model, "identifiers", None):
        id_list = [_fhir_identifier(i) for i in model.identifiers]
        id_list = [i for i in id_list if i]
        if id_list:
            res["identifier"] = id_list

    clin_status = _fhir_codeable_concept(
        getattr(model, "clinical_status_codings", None),
        model.clinical_status_text,
    )
    if clin_status:
        res["clinicalStatus"] = clin_status

    ver_status = _fhir_codeable_concept(
        getattr(model, "verification_status_codings", None),
        model.verification_status_text,
    )
    if ver_status:
        res["verificationStatus"] = ver_status

    if model.type:
        res["type"] = fhir_enum(model.type)

    if model.category:
        cat_list = [fhir_enum(c) for c in model.category]
        if cat_list:
            res["category"] = cat_list

    if model.criticality:
        res["criticality"] = fhir_enum(model.criticality)

    code_cc = _fhir_codeable_concept(
        getattr(model, "code_codings", None),
        model.code_text,
    )
    if code_cc:
        res["code"] = code_cc

    # patient (1..1)
    patient_ref = _fhir_ref(
        model.patient_reference,
        model.patient_type,
        model.patient_id,
        model.patient_display,
    )
    if patient_ref:
        res["patient"] = patient_ref

    # encounter (0..1)
    encounter_ref = _fhir_ref(
        model.encounter_reference,
        model.encounter_type,
        model.encounter_id,
        model.encounter_display,
    )
    if encounter_ref:
        res["encounter"] = encounter_ref

    # onset[x] choice
    if model.onset_date_time:
        res["onsetDateTime"] = fhir_instant(model.onset_date_time)
    elif model.onset_age:
        res["onsetAge"] = model.onset_age
    elif model.onset_period_start or model.onset_period_end:
        period: dict = {}
        if model.onset_period_start:
            period["start"] = fhir_instant(model.onset_period_start)
        if model.onset_period_end:
            period["end"] = fhir_instant(model.onset_period_end)
        res["onsetPeriod"] = period
    elif model.onset_range:
        res["onsetRange"] = model.onset_range
    elif model.onset_string:
        res["onsetString"] = model.onset_string

    if model.recorded_date:
        res["recordedDate"] = fhir_instant(model.recorded_date)

    recorder_ref = _fhir_ref(
        model.recorder_reference,
        model.recorder_type,
        model.recorder_id,
        model.recorder_display,
    )
    if recorder_ref:
        res["recorder"] = recorder_ref

    asserter_ref = _fhir_ref(
        model.asserter_reference,
        model.asserter_type,
        model.asserter_id,
        model.asserter_display,
    )
    if asserter_ref:
        res["asserter"] = asserter_ref

    if model.last_occurrence:
        res["lastOccurrence"] = fhir_instant(model.last_occurrence)

    if getattr(model, "notes", None):
        note_list = [_fhir_annotation(n) for n in model.notes]
        note_list = [n for n in note_list if n]
        if note_list:
            res["note"] = note_list

    if getattr(model, "reactions", None):
        reaction_list = [_fhir_reaction(r) for r in model.reactions]
        reaction_list = [r for r in reaction_list if r]
        if reaction_list:
            res["reaction"] = reaction_list

    if model.extension:
        res["extension"] = model.extension

    return {k: v for k, v in res.items() if v is not None}
