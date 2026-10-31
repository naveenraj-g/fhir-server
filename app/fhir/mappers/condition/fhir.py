from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.condition import ConditionModel

_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"
_COMPARATOR_SYMBOLS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}


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


def fhir_condition_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    elif ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)

    if id_use or id_system or id_value or id_type_text:
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_type_text:
            identifier["type"] = {"text": id_type_text}
        entry["identifier"] = identifier

    return entry


def _fhir_quantity(obj, prefix: str) -> dict | None:
    value = getattr(obj, f"{prefix}_value", None)
    if value is None:
        return None
    comparator = getattr(obj, f"{prefix}_comparator", None)
    result = {
        k: v
        for k, v in {
            "value": float(value),
            "comparator": _COMPARATOR_SYMBOLS.get(fhir_enum(comparator)) if comparator else None,
            "unit": getattr(obj, f"{prefix}_unit", None),
            "system": getattr(obj, f"{prefix}_system", None),
            "code": getattr(obj, f"{prefix}_code", None),
        }.items()
        if v is not None
    }
    return result or None


def _fhir_range_bound(obj, prefix: str) -> dict | None:
    value = getattr(obj, f"{prefix}_value", None)
    if value is None:
        return None
    result = {
        k: v
        for k, v in {
            "value": float(value),
            "unit": getattr(obj, f"{prefix}_unit", None),
            "system": getattr(obj, f"{prefix}_system", None),
            "code": getattr(obj, f"{prefix}_code", None),
        }.items()
        if v is not None
    }
    return result or None


def fhir_condition_identifier(i) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value

    type_codings = _fhir_coding_list(getattr(i, "type_codings", None))
    if type_codings or i.type_text:
        type_cc: dict = {}
        if type_codings:
            type_cc["coding"] = type_codings
        if i.type_text:
            type_cc["text"] = i.type_text
        entry["type"] = type_cc

    if i.period_start or i.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(i.period_start),
                "end": fhir_instant(i.period_end),
            }.items()
            if v
        }

    assigner = _fhir_reference_with_identifier_fallback(i, "assigner")
    if assigner:
        entry["assigner"] = assigner

    return entry


def fhir_condition_stage(s) -> dict:
    stage_dict: dict = {}
    summary = fhir_condition_codeable_concept(s.summary_codings, s.summary_text)
    if summary:
        stage_dict["summary"] = summary

    assessments = [
        _fhir_reference_with_identifier_fallback(a, "reference")
        for a in (s.assessments or [])
    ]
    assessments = [a for a in assessments if a]
    if assessments:
        stage_dict["assessment"] = assessments

    stage_type = fhir_condition_codeable_concept(s.type_codings, s.type_text)
    if stage_type:
        stage_dict["type"] = stage_type

    return stage_dict


def fhir_condition_evidence(e) -> dict:
    evidence_dict: dict = {}
    codes = [
        fhir_condition_codeable_concept(c.codings, c.text)
        for c in (e.codes or [])
    ]
    codes = [c for c in codes if c]
    if codes:
        evidence_dict["code"] = codes

    details = [
        _fhir_reference_with_identifier_fallback(d, "reference")
        for d in (e.details or [])
    ]
    details = [d for d in details if d]
    if details:
        evidence_dict["detail"] = details

    return evidence_dict


def fhir_condition_note(n) -> dict:
    note_dict: dict = {}
    if n.author_reference or n.author_id:
        author_ref = _fhir_reference_with_identifier_fallback(n, "author")
        if author_ref:
            note_dict["authorReference"] = author_ref
    elif n.author_string:
        note_dict["authorString"] = n.author_string

    if n.time:
        note_dict["time"] = fhir_instant(n.time)
    if n.text:
        note_dict["text"] = n.text
    return note_dict


def _fhir_meta(cond: ConditionModel) -> dict:
    meta: dict = {}
    if cond.updated_at:
        meta["lastUpdated"] = fhir_instant(cond.updated_at)

    extensions = []
    if cond.tenant_id:
        extensions.append({"url": f"{_EXT_BASE}/org-id", "valueString": cond.tenant_id})
    if cond.created_by:
        extensions.append({"url": f"{_EXT_BASE}/created-by", "valueString": cond.created_by})
    if cond.updated_by:
        extensions.append({"url": f"{_EXT_BASE}/updated-by", "valueString": cond.updated_by})
    if cond.created_at:
        extensions.append(
            {"url": f"{_EXT_BASE}/created-at", "valueDateTime": fhir_instant(cond.created_at)}
        )
    if extensions:
        meta["extension"] = extensions
    return meta


def to_fhir_condition(cond: ConditionModel) -> dict:
    result: dict = {
        "resourceType": "Condition",
        "id": str(cond.condition_id),
    }

    meta = _fhir_meta(cond)
    if meta:
        result["meta"] = meta

    if cond.extension:
        result["extension"] = cond.extension

    identifiers = [fhir_condition_identifier(i) for i in (cond.identifiers or [])]
    identifiers = [i for i in identifiers if i]
    if identifiers:
        result["identifier"] = identifiers

    clinical_status = fhir_condition_codeable_concept(
        cond.clinical_status_codings, cond.clinical_status_text
    )
    if clinical_status:
        result["clinicalStatus"] = clinical_status

    verification_status = fhir_condition_codeable_concept(
        cond.verification_status_codings, cond.verification_status_text
    )
    if verification_status:
        result["verificationStatus"] = verification_status

    categories = [
        fhir_condition_codeable_concept(cat.codings, cat.text)
        for cat in (cond.categories or [])
    ]
    categories = [cat for cat in categories if cat]
    if categories:
        result["category"] = categories

    severity = fhir_condition_codeable_concept(
        cond.severity_codings, cond.severity_text
    )
    if severity:
        result["severity"] = severity

    code = fhir_condition_codeable_concept(cond.code_codings, cond.code_text)
    if code:
        result["code"] = code

    body_sites = [
        fhir_condition_codeable_concept(b.codings, b.text)
        for b in (cond.body_sites or [])
    ]
    body_sites = [b for b in body_sites if b]
    if body_sites:
        result["bodySite"] = body_sites

    subject = _fhir_reference_with_identifier_fallback(cond, "subject")
    if subject:
        result["subject"] = subject

    encounter = _fhir_reference_with_identifier_fallback(cond, "encounter")
    if encounter:
        result["encounter"] = encounter

    # onset[x]
    if cond.onset_date_time:
        result["onsetDateTime"] = fhir_instant(cond.onset_date_time)
    elif cond.onset_age_value is not None:
        age = _fhir_quantity(cond, "onset_age")
        if age:
            result["onsetAge"] = age
    elif cond.onset_period_start or cond.onset_period_end:
        result["onsetPeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(cond.onset_period_start),
                "end": fhir_instant(cond.onset_period_end),
            }.items()
            if v
        }
    elif cond.onset_range_low_value is not None or cond.onset_range_high_value is not None:
        range_dict = {
            k: v
            for k, v in {
                "low": _fhir_range_bound(cond, "onset_range_low"),
                "high": _fhir_range_bound(cond, "onset_range_high"),
            }.items()
            if v
        }
        if range_dict:
            result["onsetRange"] = range_dict
    elif cond.onset_string:
        result["onsetString"] = cond.onset_string

    # abatement[x]
    if cond.abatement_date_time:
        result["abatementDateTime"] = fhir_instant(cond.abatement_date_time)
    elif cond.abatement_age_value is not None:
        age = _fhir_quantity(cond, "abatement_age")
        if age:
            result["abatementAge"] = age
    elif cond.abatement_period_start or cond.abatement_period_end:
        result["abatementPeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(cond.abatement_period_start),
                "end": fhir_instant(cond.abatement_period_end),
            }.items()
            if v
        }
    elif cond.abatement_range_low_value is not None or cond.abatement_range_high_value is not None:
        range_dict = {
            k: v
            for k, v in {
                "low": _fhir_range_bound(cond, "abatement_range_low"),
                "high": _fhir_range_bound(cond, "abatement_range_high"),
            }.items()
            if v
        }
        if range_dict:
            result["abatementRange"] = range_dict
    elif cond.abatement_string:
        result["abatementString"] = cond.abatement_string

    if cond.recorded_date:
        result["recordedDate"] = fhir_instant(cond.recorded_date)

    recorder = _fhir_reference_with_identifier_fallback(cond, "recorder")
    if recorder:
        result["recorder"] = recorder

    asserter = _fhir_reference_with_identifier_fallback(cond, "asserter")
    if asserter:
        result["asserter"] = asserter

    stages = [fhir_condition_stage(s) for s in (cond.stages or [])]
    stages = [s for s in stages if s]
    if stages:
        result["stage"] = stages

    evidence_list = [fhir_condition_evidence(e) for e in (cond.evidence or [])]
    evidence_list = [e for e in evidence_list if e]
    if evidence_list:
        result["evidence"] = evidence_list

    notes = [fhir_condition_note(n) for n in (cond.notes or [])]
    notes = [n for n in notes if n]
    if notes:
        result["note"] = notes

    return {k: v for k, v in result.items() if v is not None}
