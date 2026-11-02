from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.detected_issue import (
        DetectedIssueEvidenceCodeModel,
        DetectedIssueEvidenceModel,
        DetectedIssueIdentifierModel,
        DetectedIssueImplicatedModel,
        DetectedIssueMitigationModel,
        DetectedIssueModel,
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


def fhir_detected_issue_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict | None:
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
            or id_type_display
            or id_type_text
            or id_type_version
            or id_type_user_selected
        ):
            type_coding: dict = {}
            if id_type_system:
                type_coding["system"] = id_type_system
            if id_type_version:
                type_coding["version"] = id_type_version
            if id_type_code:
                type_coding["code"] = id_type_code
            if id_type_display:
                type_coding["display"] = id_type_display
            if id_type_user_selected is not None:
                type_coding["userSelected"] = id_type_user_selected
            type_cc: dict = {}
            if type_coding:
                type_cc["coding"] = [type_coding]
            if id_type_text:
                type_cc["text"] = id_type_text
            if type_cc:
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
        if identifier:
            entry["identifier"] = identifier

    return entry or None


def fhir_detected_issue_identifier(i: DetectedIssueIdentifierModel) -> dict:
    assigner_raw = getattr(i, "assigner_reference", None)
    assigner_id = getattr(i, "assigner_id", None)
    assigner_type = getattr(i, "assigner_type", None)
    assigner_display = getattr(i, "assigner_display", None)

    assigner_entry: dict = {}
    if assigner_raw:
        assigner_entry["reference"] = assigner_raw
    elif assigner_type and assigner_id:
        assigner_entry["reference"] = f"{fhir_enum(assigner_type)}/{assigner_id}"
    if assigner_display:
        assigner_entry["display"] = assigner_display

    assigner_id_use = getattr(i, "assigner_identifier_use", None)
    if (
        assigner_id_use
        or getattr(i, "assigner_identifier_system", None)
        or getattr(i, "assigner_identifier_value", None)
    ):
        assigner_ident: dict = {}
        if assigner_id_use:
            assigner_ident["use"] = fhir_enum(assigner_id_use)
        if getattr(i, "assigner_identifier_system", None):
            assigner_ident["system"] = i.assigner_identifier_system
        if getattr(i, "assigner_identifier_value", None):
            assigner_ident["value"] = i.assigner_identifier_value
        if assigner_ident:
            assigner_entry["identifier"] = assigner_ident

    period: dict = {}
    if getattr(i, "period_start", None):
        period["start"] = fhir_instant(i.period_start)
    if getattr(i, "period_end", None):
        period["end"] = fhir_instant(i.period_end)

    type_cc = fhir_detected_issue_codeable_concept(
        getattr(i, "type_codings", None), getattr(i, "type_text", None)
    )

    result = {
        "use": fhir_enum(i.use) if getattr(i, "use", None) else None,
        "type": type_cc,
        "system": getattr(i, "system", None),
        "value": getattr(i, "value", None),
        "period": period or None,
        "assigner": assigner_entry or None,
    }
    return {k: v for k, v in result.items() if v is not None}


def fhir_detected_issue_evidence(ev: DetectedIssueEvidenceModel) -> dict:
    codes = []
    for c in ev.codes or []:
        cc = fhir_detected_issue_codeable_concept(c.codings, c.text)
        if cc:
            codes.append(cc)

    details = []
    for d in ev.details or []:
        ref = _fhir_reference_with_identifier_fallback(d, "detail")
        if ref:
            details.append(ref)

    res: dict = {}
    if codes:
        res["code"] = codes
    if details:
        res["detail"] = details
    return res


def fhir_detected_issue_mitigation(m: DetectedIssueMitigationModel) -> dict:
    action = fhir_detected_issue_codeable_concept(m.action_codings, m.action_text) or {
        "text": "Mitigation action"
    }
    res: dict = {"action": action}
    if m.date:
        res["date"] = fhir_instant(m.date)
    author = _fhir_reference_with_identifier_fallback(m, "author")
    if author:
        res["author"] = author
    return res


def _fhir_meta(model: DetectedIssueModel) -> dict:
    meta: dict[str, Any] = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    elif model.created_at:
        meta["lastUpdated"] = fhir_instant(model.created_at)
    return meta


def to_fhir_detected_issue(model: DetectedIssueModel) -> dict:
    """Serializes a DetectedIssueModel ORM row to a FHIR R4 camelCase dict."""
    meta = _fhir_meta(model)
    code = fhir_detected_issue_codeable_concept(model.code_codings, model.code_text)
    patient = _fhir_reference_with_identifier_fallback(model, "patient")
    author = _fhir_reference_with_identifier_fallback(model, "author")

    period: dict = {}
    if model.identified_period_start:
        period["start"] = fhir_instant(model.identified_period_start)
    if model.identified_period_end:
        period["end"] = fhir_instant(model.identified_period_end)

    implicated = []
    for imp in model.implicated_resources or []:
        ref = _fhir_reference_with_identifier_fallback(imp, "implicated")
        if ref:
            implicated.append(ref)

    evidence = []
    for ev in model.evidence_list or []:
        ev_dict = fhir_detected_issue_evidence(ev)
        if ev_dict:
            evidence.append(ev_dict)

    mitigation = []
    for m in model.mitigations or []:
        mitigation.append(fhir_detected_issue_mitigation(m))

    identifiers = [
        fhir_detected_issue_identifier(i) for i in model.identifiers or []
    ]

    result: dict[str, Any] = {
        "resourceType": "DetectedIssue",
        "id": str(model.detected_issue_id),
        "meta": meta or None,
        "identifier": identifiers or None,
        "status": fhir_enum(model.status),
        "code": code,
        "severity": fhir_enum(model.severity) if model.severity else None,
        "patient": patient,
        "identifiedDateTime": (
            fhir_instant(model.identified_date_time)
            if model.identified_date_time
            else None
        ),
        "identifiedPeriod": period or None,
        "author": author,
        "implicated": implicated or None,
        "evidence": evidence or None,
        "detail": model.detail,
        "reference": model.reference,
        "mitigation": mitigation or None,
        "extension": model.extension or None,
    }

    return {k: v for k, v in result.items() if v is not None}
