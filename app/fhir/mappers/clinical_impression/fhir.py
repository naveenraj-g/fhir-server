from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.clinical_impression import (
        ClinicalImpressionFindingModel,
        ClinicalImpressionIdentifierModel,
        ClinicalImpressionInvestigationModel,
        ClinicalImpressionModel,
        ClinicalImpressionNoteModel,
        ClinicalImpressionProblemModel,
        ClinicalImpressionPrognosisCodeableConceptModel,
        ClinicalImpressionPrognosisReferenceModel,
        ClinicalImpressionProtocolModel,
        ClinicalImpressionSupportingInfoModel,
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


def fhir_clinical_impression_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict:
    ref_col = prefix if prefix.endswith("reference") else f"{prefix}_reference"
    disp_col = "display" if prefix == "reference" else f"{prefix}_display"
    type_col = f"{prefix}_type"
    id_col = f"{prefix}_id"

    raw_reference = getattr(obj, ref_col, None)
    ref_type = getattr(obj, type_col, None)
    ref_id = getattr(obj, id_col, None)
    display = getattr(obj, disp_col, None)

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    elif ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display

    id_prefix = "" if prefix == "reference" else f"{prefix}_"
    id_use = getattr(obj, f"{id_prefix}identifier_use", None)
    id_type_system = getattr(obj, f"{id_prefix}identifier_type_system", None)
    id_type_version = getattr(obj, f"{id_prefix}identifier_type_version", None)
    id_type_code = getattr(obj, f"{id_prefix}identifier_type_code", None)
    id_type_display = getattr(obj, f"{id_prefix}identifier_type_display", None)
    id_type_user_selected = getattr(obj, f"{id_prefix}identifier_type_user_selected", None)
    id_type_text = getattr(obj, f"{id_prefix}identifier_type_text", None)
    id_system = getattr(obj, f"{id_prefix}identifier_system", None)
    id_value = getattr(obj, f"{id_prefix}identifier_value", None)
    id_period_start = getattr(obj, f"{id_prefix}identifier_period_start", None)
    id_period_end = getattr(obj, f"{id_prefix}identifier_period_end", None)

    if (
        id_use
        or id_type_system
        or id_type_version
        or id_type_code
        or id_type_display
        or id_type_user_selected
        or id_type_text
        or id_system
        or id_value
        or id_period_start
        or id_period_end
    ):
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if (
            id_type_system
            or id_type_code
            or id_type_text
            or id_type_display
            or id_type_version
            or id_type_user_selected
        ):
            type_cc: dict = {}
            if id_type_system or id_type_code or id_type_display or id_type_version or id_type_user_selected:
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
            period: dict = {}
            if id_period_start:
                period["start"] = fhir_instant(id_period_start)
            if id_period_end:
                period["end"] = fhir_instant(id_period_end)
            identifier["period"] = period
        entry["identifier"] = identifier

    return entry


def fhir_clinical_impression_identifier(model: ClinicalImpressionIdentifierModel) -> dict:
    entry: dict = {}
    if model.use:
        entry["use"] = fhir_enum(model.use)
    type_cc = fhir_clinical_impression_codeable_concept(model.type_codings, model.type_text)
    if type_cc:
        entry["type"] = type_cc
    if model.system:
        entry["system"] = model.system
    if model.value:
        entry["value"] = model.value
    if model.period_start or model.period_end:
        period: dict = {}
        if model.period_start:
            period["start"] = fhir_instant(model.period_start)
        if model.period_end:
            period["end"] = fhir_instant(model.period_end)
        entry["period"] = period

    assigner = _fhir_reference_with_identifier_fallback(model, "assigner")
    if assigner:
        entry["assigner"] = assigner

    return entry


def fhir_clinical_impression_investigation(model: ClinicalImpressionInvestigationModel) -> dict:
    entry: dict = {}
    code_cc = fhir_clinical_impression_codeable_concept(model.code_codings, model.code_text)
    if code_cc:
        entry["code"] = code_cc
    else:
        entry["code"] = {"text": "Investigation"}

    items = []
    for it in model.items or []:
        ref_dict = _fhir_reference_with_identifier_fallback(it, "item")
        if ref_dict:
            items.append(ref_dict)
    if items:
        entry["item"] = items
    return entry


def fhir_clinical_impression_finding(model: ClinicalImpressionFindingModel) -> dict:
    entry: dict = {}
    item_cc = fhir_clinical_impression_codeable_concept(model.item_codings, model.item_codeable_concept_text)
    if item_cc:
        entry["itemCodeableConcept"] = item_cc
    item_ref = _fhir_reference_with_identifier_fallback(model, "item_reference")
    if item_ref:
        entry["itemReference"] = item_ref
    if model.basis:
        entry["basis"] = model.basis
    return entry


def fhir_clinical_impression_note(model: ClinicalImpressionNoteModel) -> dict:
    entry: dict = {}
    if model.author_string:
        entry["authorString"] = model.author_string
    elif model.author_reference or (model.author_type and model.author_id):
        ref_dict = _fhir_reference_with_identifier_fallback(model, "author")
        if ref_dict:
            entry["authorReference"] = ref_dict
    if model.time:
        entry["time"] = fhir_instant(model.time)
    entry["text"] = model.text
    return entry


def _fhir_meta(model: ClinicalImpressionModel) -> dict | None:
    meta: dict[str, Any] = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    return meta or None


def to_fhir_clinical_impression(model: ClinicalImpressionModel) -> dict:
    """Serializes a ClinicalImpressionModel ORM row to a FHIR R4 ClinicalImpression resource dict."""
    result: dict[str, Any] = {
        "resourceType": "ClinicalImpression",
        "id": str(model.clinical_impression_id),
    }

    meta = _fhir_meta(model)
    if meta:
        result["meta"] = meta

    if model.extension:
        result["extension"] = model.extension

    if model.identifiers:
        result["identifier"] = [
            fhir_clinical_impression_identifier(i) for i in model.identifiers
        ]

    result["status"] = fhir_enum(model.status)

    status_reason = fhir_clinical_impression_codeable_concept(
        model.status_reason_codings, model.status_reason_text
    )
    if status_reason:
        result["statusReason"] = status_reason

    code = fhir_clinical_impression_codeable_concept(
        model.code_codings, model.code_text
    )
    if code:
        result["code"] = code

    if model.description:
        result["description"] = model.description

    subj = _fhir_reference_with_identifier_fallback(model, "subject")
    if subj:
        result["subject"] = subj

    enc = _fhir_reference_with_identifier_fallback(model, "encounter")
    if enc:
        result["encounter"] = enc

    if model.effective_date_time:
        result["effectiveDateTime"] = fhir_instant(model.effective_date_time)
    elif model.effective_period_start or model.effective_period_end:
        period: dict[str, Any] = {}
        if model.effective_period_start:
            period["start"] = fhir_instant(model.effective_period_start)
        if model.effective_period_end:
            period["end"] = fhir_instant(model.effective_period_end)
        result["effectivePeriod"] = period

    if model.date:
        result["date"] = fhir_instant(model.date)

    assessor = _fhir_reference_with_identifier_fallback(model, "assessor")
    if assessor:
        result["assessor"] = assessor

    prev = _fhir_reference_with_identifier_fallback(model, "previous")
    if prev:
        result["previous"] = prev

    if model.problems:
        problems = [
            _fhir_reference_with_identifier_fallback(p, "problem") for p in model.problems
        ]
        if problems:
            result["problem"] = problems

    if model.investigations:
        result["investigation"] = [
            fhir_clinical_impression_investigation(inv) for inv in model.investigations
        ]

    if model.protocols:
        result["protocol"] = [p.uri for p in model.protocols if p.uri]

    if model.summary:
        result["summary"] = model.summary

    if model.findings:
        result["finding"] = [
            fhir_clinical_impression_finding(f) for f in model.findings
        ]

    if model.prognosis_codeable_concepts:
        prognosis_cc = [
            fhir_clinical_impression_codeable_concept(p.codings, p.text)
            for p in model.prognosis_codeable_concepts
        ]
        prognosis_cc = [p for p in prognosis_cc if p is not None]
        if prognosis_cc:
            result["prognosisCodeableConcept"] = prognosis_cc

    if model.prognosis_references:
        prognosis_ref = [
            _fhir_reference_with_identifier_fallback(pr, "reference")
            for pr in model.prognosis_references
        ]
        if prognosis_ref:
            result["prognosisReference"] = prognosis_ref

    if model.supporting_info:
        supporting_info = [
            _fhir_reference_with_identifier_fallback(si, "reference")
            for si in model.supporting_info
        ]
        if supporting_info:
            result["supportingInfo"] = supporting_info

    if model.notes:
        result["note"] = [
            fhir_clinical_impression_note(n) for n in model.notes
        ]

    return {k: v for k, v in result.items() if v is not None}
