"""Payload -> FHIR JSON conversion for ClinicalImpression.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(ClinicalImpressionCreateSchema / ClinicalImpressionPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.schemas.clinical_impression.input import (
        ClinicalImpressionCodeableConceptInput,
        ClinicalImpressionCreateSchema,
        ClinicalImpressionFindingInput,
        ClinicalImpressionIdentifierInput,
        ClinicalImpressionInvestigationInput,
        ClinicalImpressionNoteInput,
        ClinicalImpressionPatchSchema,
    )


def _val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _format_datetime(val: Any) -> str | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=timezone.utc)
        return val.isoformat()
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


def _coding_from_payload(c: Any) -> dict:
    if isinstance(c, dict):
        return {
            k: v
            for k, v in {
                "system": c.get("system"),
                "version": c.get("version"),
                "code": c.get("code"),
                "display": c.get("display"),
                "userSelected": c.get("user_selected"),
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


def payload_clinical_impression_codeable_concept(cc: Any) -> dict | None:
    if cc is None:
        return None
    codings = _val(cc, "coding", None)
    coding_list = [_coding_from_payload(c) for c in codings] if codings else []
    text = _val(cc, "text", None)
    result: dict[str, Any] = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _reference_with_identifier_from_payload(ref_obj: Any) -> dict | None:
    if ref_obj is None:
        return None

    ref_str = _val(ref_obj, "reference", None)
    display = _val(ref_obj, "reference_display", None)

    use = _val(ref_obj, "reference_identifier_use", None)
    type_system = _val(ref_obj, "reference_identifier_type_system", None)
    type_version = _val(ref_obj, "reference_identifier_type_version", None)
    type_code = _val(ref_obj, "reference_identifier_type_code", None)
    type_display = _val(ref_obj, "reference_identifier_type_display", None)
    type_user_selected = _val(ref_obj, "reference_identifier_type_user_selected", None)
    type_text = _val(ref_obj, "reference_identifier_type_text", None)
    system = _val(ref_obj, "reference_identifier_system", None)
    value = _val(ref_obj, "reference_identifier_value", None)
    period_start = _val(ref_obj, "reference_identifier_period_start", None)
    period_end = _val(ref_obj, "reference_identifier_period_end", None)

    has_ident = any(
        x is not None
        for x in (
            use,
            type_system,
            type_version,
            type_code,
            type_display,
            type_user_selected,
            type_text,
            system,
            value,
            period_start,
            period_end,
        )
    )

    if not ref_str and not display and not has_ident:
        return None

    entry: dict[str, Any] = {}
    if ref_str:
        entry["reference"] = ref_str
    if display:
        entry["display"] = display

    if has_ident:
        identifier: dict[str, Any] = {}
        if use:
            identifier["use"] = getattr(use, "value", str(use))
        if any(
            x is not None
            for x in (type_system, type_version, type_code, type_display, type_user_selected, type_text)
        ):
            type_cc: dict[str, Any] = {}
            if any(x is not None for x in (type_system, type_version, type_code, type_display, type_user_selected)):
                type_cc["coding"] = [
                    {
                        k: v
                        for k, v in {
                            "system": type_system,
                            "version": type_version,
                            "code": type_code,
                            "display": type_display,
                            "userSelected": type_user_selected,
                        }.items()
                        if v is not None
                    }
                ]
            if type_text:
                type_cc["text"] = type_text
            identifier["type"] = type_cc
        if system:
            identifier["system"] = system
        if value:
            identifier["value"] = value
        if period_start or period_end:
            period: dict[str, Any] = {}
            if period_start:
                period["start"] = _format_datetime(period_start)
            if period_end:
                period["end"] = _format_datetime(period_end)
            identifier["period"] = period
        entry["identifier"] = identifier

    return entry


def payload_clinical_impression_identifier(ident: Any) -> dict:
    entry: dict[str, Any] = {}
    use = _val(ident, "use", None)
    if use:
        entry["use"] = getattr(use, "value", str(use))
    type_obj = _val(ident, "type", None)
    if type_obj:
        type_cc = payload_clinical_impression_codeable_concept(type_obj)
        if type_cc:
            entry["type"] = type_cc
    system = _val(ident, "system", None)
    if system:
        entry["system"] = system
    value = _val(ident, "value", None)
    if value:
        entry["value"] = value
    period_start = _val(ident, "period_start", None)
    period_end = _val(ident, "period_end", None)
    if period_start or period_end:
        period: dict[str, Any] = {}
        if period_start:
            period["start"] = _format_datetime(period_start)
        if period_end:
            period["end"] = _format_datetime(period_end)
        entry["period"] = period

    assigner_ref = _val(ident, "assigner", None)
    assigner_display = _val(ident, "assigner_display", None)
    assigner_id_use = _val(ident, "assigner_identifier_use", None)
    assigner_id_type_system = _val(ident, "assigner_identifier_type_system", None)
    assigner_id_type_version = _val(ident, "assigner_identifier_type_version", None)
    assigner_id_type_code = _val(ident, "assigner_identifier_type_code", None)
    assigner_id_type_display = _val(ident, "assigner_identifier_type_display", None)
    assigner_id_type_user_selected = _val(ident, "assigner_identifier_type_user_selected", None)
    assigner_id_type_text = _val(ident, "assigner_identifier_type_text", None)
    assigner_id_system = _val(ident, "assigner_identifier_system", None)
    assigner_id_value = _val(ident, "assigner_identifier_value", None)
    assigner_id_period_start = _val(ident, "assigner_identifier_period_start", None)
    assigner_id_period_end = _val(ident, "assigner_identifier_period_end", None)

    has_assigner_ident = any(
        x is not None
        for x in (
            assigner_id_use,
            assigner_id_type_system,
            assigner_id_type_version,
            assigner_id_type_code,
            assigner_id_type_display,
            assigner_id_type_user_selected,
            assigner_id_type_text,
            assigner_id_system,
            assigner_id_value,
            assigner_id_period_start,
            assigner_id_period_end,
        )
    )

    if assigner_ref or assigner_display or has_assigner_ident:
        assigner_dict: dict[str, Any] = {}
        if assigner_ref:
            assigner_dict["reference"] = assigner_ref
        if assigner_display:
            assigner_dict["display"] = assigner_display
        if has_assigner_ident:
            aid: dict[str, Any] = {}
            if assigner_id_use:
                aid["use"] = getattr(assigner_id_use, "value", str(assigner_id_use))
            if any(
                x is not None
                for x in (
                    assigner_id_type_system,
                    assigner_id_type_version,
                    assigner_id_type_code,
                    assigner_id_type_display,
                    assigner_id_type_user_selected,
                    assigner_id_type_text,
                )
            ):
                at_cc: dict[str, Any] = {}
                if any(
                    x is not None
                    for x in (
                        assigner_id_type_system,
                        assigner_id_type_version,
                        assigner_id_type_code,
                        assigner_id_type_display,
                        assigner_id_type_user_selected,
                    )
                ):
                    at_cc["coding"] = [
                        {
                            k: v
                            for k, v in {
                                "system": assigner_id_type_system,
                                "version": assigner_id_type_version,
                                "code": assigner_id_type_code,
                                "display": assigner_id_type_display,
                                "userSelected": assigner_id_type_user_selected,
                            }.items()
                            if v is not None
                        }
                    ]
                if assigner_id_type_text:
                    at_cc["text"] = assigner_id_type_text
                aid["type"] = at_cc
            if assigner_id_system:
                aid["system"] = assigner_id_system
            if assigner_id_value:
                aid["value"] = assigner_id_value
            if assigner_id_period_start or assigner_id_period_end:
                aperiod: dict[str, Any] = {}
                if assigner_id_period_start:
                    aperiod["start"] = _format_datetime(assigner_id_period_start)
                if assigner_id_period_end:
                    aperiod["end"] = _format_datetime(assigner_id_period_end)
                aid["period"] = aperiod
            assigner_dict["identifier"] = aid
        entry["assigner"] = assigner_dict

    return entry


def payload_clinical_impression_investigation(inv: Any) -> dict:
    entry: dict[str, Any] = {}
    code_obj = _val(inv, "code", None)
    code_cc = payload_clinical_impression_codeable_concept(code_obj)
    entry["code"] = code_cc or {"text": "Investigation"}

    items = _val(inv, "item", None)
    if items:
        item_list = [_reference_with_identifier_from_payload(it) for it in items]
        entry["item"] = [it for it in item_list if it is not None]
    return entry


def payload_clinical_impression_finding(f: Any) -> dict:
    entry: dict[str, Any] = {}
    item_cc_obj = _val(f, "item_codeable_concept", None)
    if item_cc_obj:
        item_cc = payload_clinical_impression_codeable_concept(item_cc_obj)
        if item_cc:
            entry["itemCodeableConcept"] = item_cc
    item_ref_obj = _val(f, "item_reference", None)
    if item_ref_obj:
        item_ref = _reference_with_identifier_from_payload(item_ref_obj)
        if item_ref:
            entry["itemReference"] = item_ref
    basis = _val(f, "basis", None)
    if basis:
        entry["basis"] = basis
    return entry


def payload_clinical_impression_note(n: Any) -> dict:
    entry: dict[str, Any] = {}
    author_str = _val(n, "author_string", None)
    author_ref = _val(n, "author_reference", None)
    author_disp = _val(n, "author_display", None)

    if author_str:
        entry["authorString"] = author_str
    elif author_ref or author_disp:
        author_dict: dict[str, Any] = {}
        if author_ref:
            author_dict["reference"] = author_ref
        if author_disp:
            author_dict["display"] = author_disp
        entry["authorReference"] = author_dict

    time_val = _val(n, "time", None)
    if time_val:
        entry["time"] = _format_datetime(time_val)
    text = _val(n, "text", "")
    entry["text"] = text
    return entry


def payload_to_fhir_clinical_impression(payload: ClinicalImpressionCreateSchema) -> dict:
    """Converts a validated ClinicalImpressionCreateSchema into a FHIR R4 ClinicalImpression dict."""
    result: dict[str, Any] = {
        "resourceType": "ClinicalImpression",
    }

    if payload.extension:
        result["extension"] = list(payload.extension)

    if payload.identifier:
        result["identifier"] = [
            payload_clinical_impression_identifier(i) for i in payload.identifier if i
        ]

    result["status"] = getattr(payload.status, "value", str(payload.status))

    if payload.status_reason:
        status_reason = payload_clinical_impression_codeable_concept(payload.status_reason)
        if status_reason:
            result["statusReason"] = status_reason

    if payload.code:
        code = payload_clinical_impression_codeable_concept(payload.code)
        if code:
            result["code"] = code

    if payload.description:
        result["description"] = payload.description

    subj = _reference_with_identifier_from_payload(payload.subject)
    if subj:
        result["subject"] = subj

    if payload.encounter:
        enc = _reference_with_identifier_from_payload(payload.encounter)
        if enc:
            result["encounter"] = enc

    if payload.effective_date_time:
        result["effectiveDateTime"] = _format_datetime(payload.effective_date_time)
    elif payload.effective_period_start or payload.effective_period_end:
        period: dict[str, Any] = {}
        if payload.effective_period_start:
            period["start"] = _format_datetime(payload.effective_period_start)
        if payload.effective_period_end:
            period["end"] = _format_datetime(payload.effective_period_end)
        result["effectivePeriod"] = period

    if payload.date:
        result["date"] = _format_datetime(payload.date)

    if payload.assessor:
        assessor = _reference_with_identifier_from_payload(payload.assessor)
        if assessor:
            result["assessor"] = assessor

    if payload.previous:
        prev = _reference_with_identifier_from_payload(payload.previous)
        if prev:
            result["previous"] = prev

    if payload.problem:
        problem_list = [
            _reference_with_identifier_from_payload(p) for p in payload.problem if p
        ]
        problem_list = [p for p in problem_list if p is not None]
        if problem_list:
            result["problem"] = problem_list

    if payload.investigation:
        result["investigation"] = [
            payload_clinical_impression_investigation(inv)
            for inv in payload.investigation
            if inv
        ]

    if payload.protocol:
        result["protocol"] = [pr for pr in payload.protocol if pr]

    if payload.summary:
        result["summary"] = payload.summary

    if payload.finding:
        result["finding"] = [
            payload_clinical_impression_finding(f) for f in payload.finding if f
        ]

    if payload.prognosis_codeable_concept:
        prognosis_cc = [
            payload_clinical_impression_codeable_concept(p)
            for p in payload.prognosis_codeable_concept
            if p
        ]
        prognosis_cc = [p for p in prognosis_cc if p is not None]
        if prognosis_cc:
            result["prognosisCodeableConcept"] = prognosis_cc

    if payload.prognosis_reference:
        prognosis_ref = [
            _reference_with_identifier_from_payload(pr)
            for pr in payload.prognosis_reference
            if pr
        ]
        prognosis_ref = [pr for pr in prognosis_ref if pr is not None]
        if prognosis_ref:
            result["prognosisReference"] = prognosis_ref

    if payload.supporting_info:
        supporting_info = [
            _reference_with_identifier_from_payload(si)
            for si in payload.supporting_info
            if si
        ]
        supporting_info = [si for si in supporting_info if si is not None]
        if supporting_info:
            result["supportingInfo"] = supporting_info

    if payload.note:
        result["note"] = [
            payload_clinical_impression_note(n) for n in payload.note if n
        ]

    return {k: v for k, v in result.items() if v is not None}


def patch_fragment_to_fhir_clinical_impression(
    payload: ClinicalImpressionPatchSchema,
) -> tuple[dict, set[str]]:
    """Converts a ClinicalImpressionPatchSchema into a partial FHIR dict and a set of touched FHIR keys."""
    provided = payload.model_fields_set
    fragment: dict[str, Any] = {}
    touched: set[str] = set()

    if "status" in provided:
        touched.add("status")
        fragment["status"] = (
            getattr(payload.status, "value", str(payload.status))
            if payload.status is not None
            else None
        )

    if "status_reason" in provided:
        touched.add("statusReason")
        fragment["statusReason"] = (
            payload_clinical_impression_codeable_concept(payload.status_reason)
            if payload.status_reason is not None
            else None
        )

    if "code" in provided:
        touched.add("code")
        fragment["code"] = (
            payload_clinical_impression_codeable_concept(payload.code)
            if payload.code is not None
            else None
        )

    if "description" in provided:
        touched.add("description")
        fragment["description"] = payload.description

    if "subject" in provided:
        touched.add("subject")
        fragment["subject"] = (
            _reference_with_identifier_from_payload(payload.subject)
            if payload.subject is not None
            else None
        )

    if "encounter" in provided:
        touched.add("encounter")
        fragment["encounter"] = (
            _reference_with_identifier_from_payload(payload.encounter)
            if payload.encounter is not None
            else None
        )

    if "effective_date_time" in provided or "effective_period_start" in provided or "effective_period_end" in provided:
        touched.update({"effectiveDateTime", "effectivePeriod"})
        if payload.effective_date_time is not None:
            fragment["effectiveDateTime"] = _format_datetime(payload.effective_date_time)
            fragment["effectivePeriod"] = None
        elif payload.effective_period_start is not None or payload.effective_period_end is not None:
            fragment["effectivePeriod"] = {
                k: v
                for k, v in {
                    "start": _format_datetime(payload.effective_period_start) if payload.effective_period_start else None,
                    "end": _format_datetime(payload.effective_period_end) if payload.effective_period_end else None,
                }.items()
                if v is not None
            }
            fragment["effectiveDateTime"] = None
        else:
            fragment["effectiveDateTime"] = None
            fragment["effectivePeriod"] = None

    if "date" in provided:
        touched.add("date")
        fragment["date"] = (
            _format_datetime(payload.date) if payload.date is not None else None
        )

    if "assessor" in provided:
        touched.add("assessor")
        fragment["assessor"] = (
            _reference_with_identifier_from_payload(payload.assessor)
            if payload.assessor is not None
            else None
        )

    if "previous" in provided:
        touched.add("previous")
        fragment["previous"] = (
            _reference_with_identifier_from_payload(payload.previous)
            if payload.previous is not None
            else None
        )

    if "problem" in provided:
        touched.add("problem")
        fragment["problem"] = (
            [_reference_with_identifier_from_payload(p) for p in payload.problem if p]
            if payload.problem is not None
            else None
        )

    if "investigation" in provided:
        touched.add("investigation")
        fragment["investigation"] = (
            [payload_clinical_impression_investigation(inv) for inv in payload.investigation if inv]
            if payload.investigation is not None
            else None
        )

    if "protocol" in provided:
        touched.add("protocol")
        fragment["protocol"] = (
            list(payload.protocol) if payload.protocol is not None else None
        )

    if "summary" in provided:
        touched.add("summary")
        fragment["summary"] = payload.summary

    if "finding" in provided:
        touched.add("finding")
        fragment["finding"] = (
            [payload_clinical_impression_finding(f) for f in payload.finding if f]
            if payload.finding is not None
            else None
        )

    if "prognosis_codeable_concept" in provided:
        touched.add("prognosisCodeableConcept")
        fragment["prognosisCodeableConcept"] = (
            [payload_clinical_impression_codeable_concept(p) for p in payload.prognosis_codeable_concept if p]
            if payload.prognosis_codeable_concept is not None
            else None
        )

    if "prognosis_reference" in provided:
        touched.add("prognosisReference")
        fragment["prognosisReference"] = (
            [_reference_with_identifier_from_payload(pr) for pr in payload.prognosis_reference if pr]
            if payload.prognosis_reference is not None
            else None
        )

    if "supporting_info" in provided:
        touched.add("supportingInfo")
        fragment["supportingInfo"] = (
            [_reference_with_identifier_from_payload(si) for si in payload.supporting_info if si]
            if payload.supporting_info is not None
            else None
        )

    if "note" in provided:
        touched.add("note")
        fragment["note"] = (
            [payload_clinical_impression_note(n) for n in payload.note if n]
            if payload.note is not None
            else None
        )

    if "identifier" in provided:
        touched.add("identifier")
        fragment["identifier"] = (
            [payload_clinical_impression_identifier(i) for i in payload.identifier if i]
            if payload.identifier is not None
            else None
        )

    if "extension" in provided:
        touched.add("extension")
        fragment["extension"] = (
            list(payload.extension) if payload.extension is not None else None
        )

    return fragment, touched
