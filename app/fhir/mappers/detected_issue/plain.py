from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.detected_issue import (
        DetectedIssueEvidenceCodeModel,
        DetectedIssueEvidenceModel,
        DetectedIssueIdentifierModel,
        DetectedIssueImplicatedModel,
        DetectedIssueMitigationModel,
        DetectedIssueModel,
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


def plain_detected_issue_codeable_concept(codings, text: str | None) -> dict | None:
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


def plain_detected_issue_identifier(i: DetectedIssueIdentifierModel) -> dict:
    assigner_raw = getattr(i, "assigner_reference", None)
    assigner_id = getattr(i, "assigner_id", None)
    assigner_type = getattr(i, "assigner_type", None)
    assigner_display = getattr(i, "assigner_display", None)
    assigner_ref_str = assigner_raw
    if not assigner_ref_str and assigner_type and assigner_id:
        assigner_ref_str = f"{fhir_enum(assigner_type)}/{assigner_id}"

    assigner_id_use = getattr(i, "assigner_identifier_use", None)

    type_cc = plain_detected_issue_codeable_concept(
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


def plain_detected_issue_evidence(ev: DetectedIssueEvidenceModel) -> dict:
    codes = []
    for c in ev.codes or []:
        cc = plain_detected_issue_codeable_concept(c.codings, c.text)
        if cc:
            codes.append(cc)

    details = []
    for d in ev.details or []:
        details.append(plain_reference_with_identifier_fallback(d, "detail"))

    return {
        "id": ev.id,
        "code": codes if codes else None,
        "detail": details if details else None,
    }


def plain_detected_issue_mitigation(m: DetectedIssueMitigationModel) -> dict:
    action = plain_detected_issue_codeable_concept(m.action_codings, m.action_text) or {
        "text": "Mitigation action",
        "coding": None,
    }
    author = plain_reference_with_identifier_fallback(m, "author")
    has_author = any(v is not None for v in author.values())

    return {
        "id": m.id,
        "action": action,
        "date": m.date,
        "author": author if has_author else None,
    }


def to_plain_detected_issue(model: DetectedIssueModel) -> dict:
    """Serializes a DetectedIssueModel ORM row to a plain snake_case dict."""
    code = plain_detected_issue_codeable_concept(
        model.code_codings, model.code_text
    )

    patient = plain_reference_with_identifier_fallback(model, "patient")
    has_patient = any(v is not None for v in patient.values())

    author = plain_reference_with_identifier_fallback(model, "author")
    has_author = any(v is not None for v in author.values())

    implicated = []
    for imp in model.implicated_resources or []:
        implicated.append(plain_reference_with_identifier_fallback(imp, "implicated"))

    evidence = []
    for ev in model.evidence_list or []:
        evidence.append(plain_detected_issue_evidence(ev))

    mitigation = []
    for m in model.mitigations or []:
        mitigation.append(plain_detected_issue_mitigation(m))

    identifiers = [
        plain_detected_issue_identifier(i) for i in model.identifiers or []
    ]

    return {
        "id": model.detected_issue_id,
        "status": fhir_enum(model.status),
        "code": code,
        "severity": fhir_enum(model.severity) if model.severity else None,
        "patient": patient if has_patient else None,
        "identified_date_time": model.identified_date_time,
        "identified_period_start": model.identified_period_start,
        "identified_period_end": model.identified_period_end,
        "author": author if has_author else None,
        "implicated": implicated if implicated else None,
        "evidence": evidence if evidence else None,
        "detail": model.detail,
        "reference": model.reference,
        "mitigation": mitigation if mitigation else None,
        "identifier": identifiers if identifiers else None,
        "extension": model.extension or None,
    }
