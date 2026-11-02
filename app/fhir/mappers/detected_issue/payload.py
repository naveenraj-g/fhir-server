"""Payload -> FHIR JSON conversion for DetectedIssue.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(DetectedIssueCreateSchema / DetectedIssuePatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.detected_issue.input import (
        DetectedIssueCodeableConceptInput,
        DetectedIssueCreateSchema,
        DetectedIssueEvidenceInput,
        DetectedIssueIdentifierInput,
        DetectedIssueMitigationInput,
        DetectedIssuePatchSchema,
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


def payload_detected_issue_codeable_concept(cc: Any) -> dict | None:
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

    has_ref = bool(ref_str)
    has_display = bool(display)
    has_ident = any(
        x is not None
        for x in [
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
        ]
    )

    if not (has_ref or has_display or has_ident):
        return None

    out: dict[str, Any] = {}
    if ref_str:
        out["reference"] = ref_str
    if display:
        out["display"] = display

    if has_ident:
        ident: dict[str, Any] = {}
        if use is not None:
            ident["use"] = fhir_enum(use)
        if any(
            x is not None
            for x in [
                type_system,
                type_version,
                type_code,
                type_display,
                type_user_selected,
                type_text,
            ]
        ):
            tc: dict[str, Any] = {}
            if type_system is not None:
                tc["system"] = type_system
            if type_version is not None:
                tc["version"] = type_version
            if type_code is not None:
                tc["code"] = type_code
            if type_display is not None:
                tc["display"] = type_display
            if type_user_selected is not None:
                tc["userSelected"] = type_user_selected
            t_cc: dict[str, Any] = {}
            if tc:
                t_cc["coding"] = [tc]
            if type_text is not None:
                t_cc["text"] = type_text
            if t_cc:
                ident["type"] = t_cc
        if system is not None:
            ident["system"] = system
        if value is not None:
            ident["value"] = value
        if period_start is not None or period_end is not None:
            p: dict[str, Any] = {}
            if period_start is not None:
                p["start"] = _format_datetime(period_start)
            if period_end is not None:
                p["end"] = _format_datetime(period_end)
            if p:
                ident["period"] = p
        if ident:
            out["identifier"] = ident

    return out or None


def payload_detected_issue_identifier(i: Any) -> dict:
    if i is None:
        return {}
    res: dict[str, Any] = {}
    use = _val(i, "use")
    if use is not None:
        res["use"] = fhir_enum(use)
    t = payload_detected_issue_codeable_concept(_val(i, "type"))
    if t:
        res["type"] = t
    system = _val(i, "system")
    if system is not None:
        res["system"] = system
    value = _val(i, "value")
    if value is not None:
        res["value"] = value

    p_start = _val(i, "period_start")
    p_end = _val(i, "period_end")
    if p_start or p_end:
        period: dict[str, Any] = {}
        if p_start:
            period["start"] = _format_datetime(p_start)
        if p_end:
            period["end"] = _format_datetime(p_end)
        res["period"] = period

    assigner_ref = _val(i, "assigner")
    assigner_disp = _val(i, "assigner_display")
    as_use = _val(i, "assigner_identifier_use")
    as_sys = _val(i, "assigner_identifier_system")
    as_val = _val(i, "assigner_identifier_value")

    has_assigner = any(
        x is not None
        for x in [
            assigner_ref,
            assigner_disp,
            as_use,
            as_sys,
            as_val,
        ]
    )
    if has_assigner:
        assigner: dict[str, Any] = {}
        if assigner_ref:
            assigner["reference"] = assigner_ref
        if assigner_disp:
            assigner["display"] = assigner_disp
        if as_use or as_sys or as_val:
            a_ident: dict[str, Any] = {}
            if as_use:
                a_ident["use"] = fhir_enum(as_use)
            if as_sys:
                a_ident["system"] = as_sys
            if as_val:
                a_ident["value"] = as_val
            assigner["identifier"] = a_ident
        res["assigner"] = assigner

    return res


def payload_detected_issue_evidence(ev: Any) -> dict:
    if ev is None:
        return {}
    codes = [
        payload_detected_issue_codeable_concept(c)
        for c in (_val(ev, "code") or [])
        if c
    ]
    codes = [c for c in codes if c]
    details = [
        _reference_with_identifier_from_payload(d)
        for d in (_val(ev, "detail") or [])
        if d
    ]
    details = [d for d in details if d]

    res: dict[str, Any] = {}
    if codes:
        res["code"] = codes
    if details:
        res["detail"] = details
    return res


def payload_detected_issue_mitigation(m: Any) -> dict:
    if m is None:
        return {}
    action = payload_detected_issue_codeable_concept(_val(m, "action")) or {
        "text": "Mitigation action"
    }
    res: dict[str, Any] = {"action": action}
    date = _val(m, "date")
    if date:
        res["date"] = _format_datetime(date)
    author = _reference_with_identifier_from_payload(_val(m, "author"))
    if author:
        res["author"] = author
    return res


def payload_to_fhir_detected_issue(payload: DetectedIssueCreateSchema) -> dict:
    """Convert DetectedIssueCreateSchema directly into a FHIR R4 JSON dict for pre-write validation."""
    code = payload_detected_issue_codeable_concept(payload.code)
    patient = _reference_with_identifier_from_payload(payload.patient)
    author = _reference_with_identifier_from_payload(payload.author)

    period: dict[str, Any] = {}
    if payload.identified_period_start:
        period["start"] = _format_datetime(payload.identified_period_start)
    if payload.identified_period_end:
        period["end"] = _format_datetime(payload.identified_period_end)

    implicated = []
    for imp in payload.implicated or []:
        ref = _reference_with_identifier_from_payload(imp)
        if ref:
            implicated.append(ref)

    evidence = []
    for ev in payload.evidence or []:
        ev_dict = payload_detected_issue_evidence(ev)
        if ev_dict:
            evidence.append(ev_dict)

    mitigation = []
    for m in payload.mitigation or []:
        mitigation.append(payload_detected_issue_mitigation(m))

    identifiers = [
        payload_detected_issue_identifier(i)
        for i in payload.identifier or []
    ]
    identifiers = [i for i in identifiers if i]

    result: dict[str, Any] = {
        "resourceType": "DetectedIssue",
        "identifier": identifiers or None,
        "status": fhir_enum(payload.status),
        "code": code,
        "severity": fhir_enum(payload.severity) if payload.severity else None,
        "patient": patient,
        "identifiedDateTime": (
            _format_datetime(payload.identified_date_time)
            if payload.identified_date_time
            else None
        ),
        "identifiedPeriod": period or None,
        "author": author,
        "implicated": implicated or None,
        "evidence": evidence or None,
        "detail": payload.detail,
        "reference": payload.reference,
        "mitigation": mitigation or None,
        "extension": payload.extension or None,
    }

    return {k: v for k, v in result.items() if v is not None}


def patch_fragment_to_fhir_detected_issue(
    payload: DetectedIssuePatchSchema,
) -> tuple[dict, set[str]]:
    """Convert DetectedIssuePatchSchema into a partial FHIR R4 JSON dict and touched fields set."""
    provided = payload.model_dump(exclude_unset=True)
    fragment: dict[str, Any] = {}
    touched: set[str] = set()

    if "status" in provided:
        touched.add("status")
        fragment["status"] = (
            fhir_enum(payload.status) if payload.status is not None else None
        )

    if "code" in provided:
        touched.add("code")
        fragment["code"] = (
            payload_detected_issue_codeable_concept(payload.code)
            if payload.code is not None
            else None
        )

    if "severity" in provided:
        touched.add("severity")
        fragment["severity"] = (
            fhir_enum(payload.severity) if payload.severity is not None else None
        )

    if "patient" in provided:
        touched.add("patient")
        fragment["patient"] = (
            _reference_with_identifier_from_payload(payload.patient)
            if payload.patient is not None
            else None
        )

    if (
        "identified_date_time" in provided
        or "identified_period_start" in provided
        or "identified_period_end" in provided
    ):
        touched.update({"identifiedDateTime", "identifiedPeriod"})
        if payload.identified_date_time is not None:
            fragment["identifiedDateTime"] = _format_datetime(payload.identified_date_time)
            fragment["identifiedPeriod"] = None
        elif (
            payload.identified_period_start is not None
            or payload.identified_period_end is not None
        ):
            p = {
                k: v
                for k, v in {
                    "start": _format_datetime(payload.identified_period_start)
                    if payload.identified_period_start
                    else None,
                    "end": _format_datetime(payload.identified_period_end)
                    if payload.identified_period_end
                    else None,
                }.items()
                if v is not None
            }
            fragment["identifiedPeriod"] = p or None
            fragment["identifiedDateTime"] = None
        else:
            fragment["identifiedDateTime"] = None
            fragment["identifiedPeriod"] = None

    if "author" in provided:
        touched.add("author")
        fragment["author"] = (
            _reference_with_identifier_from_payload(payload.author)
            if payload.author is not None
            else None
        )

    if "implicated" in provided:
        touched.add("implicated")
        fragment["implicated"] = (
            [
                _reference_with_identifier_from_payload(imp)
                for imp in payload.implicated
                if imp
            ]
            if payload.implicated is not None
            else None
        )

    if "evidence" in provided:
        touched.add("evidence")
        fragment["evidence"] = (
            [
                payload_detected_issue_evidence(ev)
                for ev in payload.evidence
                if ev
            ]
            if payload.evidence is not None
            else None
        )

    if "detail" in provided:
        touched.add("detail")
        fragment["detail"] = payload.detail

    if "reference" in provided:
        touched.add("reference")
        fragment["reference"] = payload.reference

    if "mitigation" in provided:
        touched.add("mitigation")
        fragment["mitigation"] = (
            [
                payload_detected_issue_mitigation(m)
                for m in payload.mitigation
                if m
            ]
            if payload.mitigation is not None
            else None
        )

    if "identifier" in provided:
        touched.add("identifier")
        fragment["identifier"] = (
            [
                payload_detected_issue_identifier(i)
                for i in payload.identifier
                if i
            ]
            if payload.identifier is not None
            else None
        )

    if "extension" in provided:
        touched.add("extension")
        fragment["extension"] = (
            dict(payload.extension) if payload.extension is not None else None
        )

    return fragment, touched
