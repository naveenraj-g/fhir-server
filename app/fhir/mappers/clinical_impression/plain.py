from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

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


def plain_coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
        }
        if any(v is not None for v in entry.values()):
            result.append(entry)
    return result


def plain_clinical_impression_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = plain_coding_list(codings)
    if not coding_list and not text:
        return None
    return {
        "coding": coding_list if coding_list else None,
        "text": text,
    }


def plain_reference_with_identifier_fallback(obj, prefix: str) -> dict:
    ref_col = prefix if prefix.endswith("reference") else f"{prefix}_reference"
    disp_col = "display" if prefix == "reference" else f"{prefix}_display"
    type_col = f"{prefix}_type"
    id_col = f"{prefix}_id"

    raw_reference = getattr(obj, ref_col, None)
    ref_type = getattr(obj, type_col, None)
    ref_id = getattr(obj, id_col, None)
    display = getattr(obj, disp_col, None)

    ref_str = raw_reference
    if not ref_str and ref_type and ref_id:
        ref_str = f"{fhir_enum(ref_type)}/{ref_id}"

    id_prefix = "" if prefix == "reference" else f"{prefix}_"
    id_use = getattr(obj, f"{id_prefix}identifier_use", None)

    return {
        "reference": ref_str,
        "type": fhir_enum(ref_type) if ref_type else None,
        "id": ref_id,
        "display": display,
        "identifier_use": fhir_enum(id_use) if id_use else None,
        "identifier_type_system": getattr(obj, f"{id_prefix}identifier_type_system", None),
        "identifier_type_version": getattr(obj, f"{id_prefix}identifier_type_version", None),
        "identifier_type_code": getattr(obj, f"{id_prefix}identifier_type_code", None),
        "identifier_type_display": getattr(obj, f"{id_prefix}identifier_type_display", None),
        "identifier_type_user_selected": getattr(obj, f"{id_prefix}identifier_type_user_selected", None),
        "identifier_type_text": getattr(obj, f"{id_prefix}identifier_type_text", None),
        "identifier_system": getattr(obj, f"{id_prefix}identifier_system", None),
        "identifier_value": getattr(obj, f"{id_prefix}identifier_value", None),
        "identifier_period_start": getattr(obj, f"{id_prefix}identifier_period_start", None),
        "identifier_period_end": getattr(obj, f"{id_prefix}identifier_period_end", None),
    }


def plain_clinical_impression_identifier(i: ClinicalImpressionIdentifierModel) -> dict:
    assigner_raw = getattr(i, "assigner_reference", None)
    assigner_id = getattr(i, "assigner_id", None)
    assigner_type = getattr(i, "assigner_type", None)
    assigner_display = getattr(i, "assigner_display", None)
    assigner_ref_str = assigner_raw
    if not assigner_ref_str and assigner_type and assigner_id:
        assigner_ref_str = f"{fhir_enum(assigner_type)}/{assigner_id}"

    assigner_id_use = getattr(i, "assigner_identifier_use", None)

    type_cc = plain_clinical_impression_codeable_concept(
        getattr(i, "type_codings", None), getattr(i, "type_text", None)
    )

    return {
        "id": i.id,
        "use": fhir_enum(i.use) if getattr(i, "use", None) else None,
        "type": type_cc,
        "system": getattr(i, "system", None),
        "value": getattr(i, "value", None),
        "period_start": getattr(i, "period_start", None),
        "period_end": getattr(i, "period_end", None),
        "assigner_reference": assigner_ref_str,
        "assigner_type": fhir_enum(assigner_type) if assigner_type else None,
        "assigner_id": assigner_id,
        "assigner_display": assigner_display,
        "assigner_identifier_use": fhir_enum(assigner_id_use) if assigner_id_use else None,
        "assigner_identifier_type_system": getattr(i, "assigner_identifier_type_system", None),
        "assigner_identifier_type_version": getattr(i, "assigner_identifier_type_version", None),
        "assigner_identifier_type_code": getattr(i, "assigner_identifier_type_code", None),
        "assigner_identifier_type_display": getattr(i, "assigner_identifier_type_display", None),
        "assigner_identifier_type_user_selected": getattr(i, "assigner_identifier_type_user_selected", None),
        "assigner_identifier_type_text": getattr(i, "assigner_identifier_type_text", None),
        "assigner_identifier_system": getattr(i, "assigner_identifier_system", None),
        "assigner_identifier_value": getattr(i, "assigner_identifier_value", None),
        "assigner_identifier_period_start": getattr(i, "assigner_identifier_period_start", None),
        "assigner_identifier_period_end": getattr(i, "assigner_identifier_period_end", None),
    }


def plain_clinical_impression_investigation(model: ClinicalImpressionInvestigationModel) -> dict:
    code_cc = plain_clinical_impression_codeable_concept(model.code_codings, model.code_text)
    items = []
    for it in model.items or []:
        items.append(plain_reference_with_identifier_fallback(it, "item"))
    return {
        "id": model.id,
        "code": code_cc or {"text": "Investigation", "coding": None},
        "item": items if items else None,
    }


def plain_clinical_impression_finding(model: ClinicalImpressionFindingModel) -> dict:
    item_cc = plain_clinical_impression_codeable_concept(model.item_codings, model.item_codeable_concept_text)
    item_ref = plain_reference_with_identifier_fallback(model, "item_reference")
    has_ref = any(v is not None for v in item_ref.values())
    return {
        "id": model.id,
        "item_codeable_concept": item_cc,
        "item_reference": item_ref if has_ref else None,
        "basis": model.basis,
    }


def plain_clinical_impression_note(n: ClinicalImpressionNoteModel) -> dict:
    author_raw = getattr(n, "author_reference", None)
    author_type = getattr(n, "author_type", None)
    author_id = getattr(n, "author_id", None)
    author_ref_str = author_raw
    if not author_ref_str and author_type and author_id:
        author_ref_str = f"{fhir_enum(author_type)}/{author_id}"

    id_use = getattr(n, "author_identifier_use", None)

    return {
        "id": n.id,
        "author_string": getattr(n, "author_string", None),
        "author_reference": author_ref_str,
        "author_type": fhir_enum(author_type) if author_type else None,
        "author_id": author_id,
        "author_display": getattr(n, "author_display", None),
        "author_identifier_use": fhir_enum(id_use) if id_use else None,
        "author_identifier_type_system": getattr(n, "author_identifier_type_system", None),
        "author_identifier_type_version": getattr(n, "author_identifier_type_version", None),
        "author_identifier_type_code": getattr(n, "author_identifier_type_code", None),
        "author_identifier_type_display": getattr(n, "author_identifier_type_display", None),
        "author_identifier_type_user_selected": getattr(n, "author_identifier_type_user_selected", None),
        "author_identifier_type_text": getattr(n, "author_identifier_type_text", None),
        "author_identifier_system": getattr(n, "author_identifier_system", None),
        "author_identifier_value": getattr(n, "author_identifier_value", None),
        "author_identifier_period_start": getattr(n, "author_identifier_period_start", None),
        "author_identifier_period_end": getattr(n, "author_identifier_period_end", None),
        "time": getattr(n, "time", None),
        "text": n.text,
    }


def to_plain_clinical_impression(model: ClinicalImpressionModel) -> dict:
    """Serializes a ClinicalImpressionModel ORM row to a plain snake_case dict."""
    status_reason = plain_clinical_impression_codeable_concept(
        model.status_reason_codings, model.status_reason_text
    )
    code = plain_clinical_impression_codeable_concept(
        model.code_codings, model.code_text
    )

    subj = plain_reference_with_identifier_fallback(model, "subject")
    enc = plain_reference_with_identifier_fallback(model, "encounter")
    has_enc = any(v is not None for v in enc.values())

    assessor = plain_reference_with_identifier_fallback(model, "assessor")
    has_assessor = any(v is not None for v in assessor.values())

    prev = plain_reference_with_identifier_fallback(model, "previous")
    has_prev = any(v is not None for v in prev.values())

    problems = []
    for p in model.problems or []:
        problems.append(plain_reference_with_identifier_fallback(p, "problem"))

    investigations = []
    for inv in model.investigations or []:
        investigations.append(plain_clinical_impression_investigation(inv))

    protocols = [p.uri for p in model.protocols or [] if p.uri]

    findings = []
    for f in model.findings or []:
        findings.append(plain_clinical_impression_finding(f))

    prognosis_ccs = []
    for p in model.prognosis_codeable_concepts or []:
        cc = plain_clinical_impression_codeable_concept(p.codings, p.text)
        if cc:
            prognosis_ccs.append(cc)

    prognosis_refs = []
    for pr in model.prognosis_references or []:
        prognosis_refs.append(plain_reference_with_identifier_fallback(pr, "reference"))

    supporting_infos = []
    for si in model.supporting_info or []:
        supporting_infos.append(plain_reference_with_identifier_fallback(si, "reference"))

    notes = []
    for n in model.notes or []:
        notes.append(plain_clinical_impression_note(n))

    identifiers = []
    for i in model.identifiers or []:
        identifiers.append(plain_clinical_impression_identifier(i))

    return {
        "id": model.clinical_impression_id,
        "status": fhir_enum(model.status),
        "status_reason": status_reason,
        "code": code,
        "description": model.description,
        "subject": subj,
        "encounter": enc if has_enc else None,
        "effective_date_time": model.effective_date_time,
        "effective_period_start": model.effective_period_start,
        "effective_period_end": model.effective_period_end,
        "date": model.date,
        "assessor": assessor if has_assessor else None,
        "previous": prev if has_prev else None,
        "problem": problems if problems else None,
        "investigation": investigations if investigations else None,
        "protocol": protocols if protocols else None,
        "summary": model.summary,
        "finding": findings if findings else None,
        "prognosis_codeable_concept": prognosis_ccs if prognosis_ccs else None,
        "prognosis_reference": prognosis_refs if prognosis_refs else None,
        "supporting_info": supporting_infos if supporting_infos else None,
        "note": notes if notes else None,
        "identifier": identifiers if identifiers else None,
        "extension": model.extension or None,
    }
