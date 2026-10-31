from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.diagnostic_report import DiagnosticReportModel


def _plain_reference(obj, prefix: str) -> dict | None:
    ref = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)
    if not (ref or ref_type or ref_id or display):
        return None
    return {
        "reference": ref,
        "reference_type": fhir_enum(ref_type) if ref_type else None,
        "reference_id": ref_id,
        "reference_display": display,
    }


def _plain_reference_row(obj, row_id: int) -> dict:
    return {
        "id": row_id,
        "reference": obj.reference_reference,
        "reference_type": fhir_enum(obj.reference_type) if obj.reference_type else None,
        "reference_id": obj.reference_id,
        "reference_display": obj.reference_display,
    }


def _plain_identifier(obj, prefix: str = "") -> dict | None:
    p = prefix
    use = getattr(obj, f"{p}use", None)
    type_text = getattr(obj, f"{p}type_text", None)
    system = getattr(obj, f"{p}system", None)
    value = getattr(obj, f"{p}value", None)
    assigner_reference = getattr(obj, f"{p}assigner_reference", None)
    assigner_id = getattr(obj, f"{p}assigner_id", None)
    codings_attr = f"{p}type_codings" if p else "type_codings"
    codings = getattr(obj, codings_attr, None)
    if not (use or type_text or system or value or codings or assigner_reference or assigner_id):
        return None
    assigner_type = getattr(obj, f"{p}assigner_type", None)
    period_start = getattr(obj, f"{p}period_start", None)
    period_end = getattr(obj, f"{p}period_end", None)
    return {
        "use": fhir_enum(use) if use else None,
        "type_codings": [
            {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "user_selected": c.user_selected,
            }
            for c in (codings or [])
        ]
        or None,
        "type_text": type_text,
        "system": system,
        "value": value,
        "period_start": period_start.isoformat() if period_start else None,
        "period_end": period_end.isoformat() if period_end else None,
        "assigner": assigner_reference
        or (f"{fhir_enum(assigner_type)}/{assigner_id}" if assigner_type and assigner_id else None),
        "assigner_id": assigner_id,
        "assigner_display": getattr(obj, f"{p}assigner_display", None),
        "assigner_identifier_use": (
            fhir_enum(v) if (v := getattr(obj, f"{p}assigner_identifier_use", None)) else None
        ),
        "assigner_identifier_type_system": getattr(obj, f"{p}assigner_identifier_type_system", None),
        "assigner_identifier_type_version": getattr(obj, f"{p}assigner_identifier_type_version", None),
        "assigner_identifier_type_code": getattr(obj, f"{p}assigner_identifier_type_code", None),
        "assigner_identifier_type_display": getattr(obj, f"{p}assigner_identifier_type_display", None),
        "assigner_identifier_type_text": getattr(obj, f"{p}assigner_identifier_type_text", None),
        "assigner_identifier_type_user_selected": getattr(obj, f"{p}assigner_identifier_type_user_selected", None),
        "assigner_identifier_system": getattr(obj, f"{p}assigner_identifier_system", None),
        "assigner_identifier_value": getattr(obj, f"{p}assigner_identifier_value", None),
        "assigner_identifier_period_start": (
            v.isoformat() if (v := getattr(obj, f"{p}assigner_identifier_period_start", None)) else None
        ),
        "assigner_identifier_period_end": (
            v.isoformat() if (v := getattr(obj, f"{p}assigner_identifier_period_end", None)) else None
        ),
    }


def _plain_codeable_concept(codings, text: str | None) -> dict | None:
    if not (codings or text):
        return None
    return {
        "codings": [
            {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "user_selected": c.user_selected,
            }
            for c in (codings or [])
        ]
        or None,
        "text": text,
    }


def _plain_media(m) -> dict:
    return {
        "id": m.id,
        "comment": m.comment,
        "link": m.link_reference
        or (f"{fhir_enum(m.link_type)}/{m.link_id}" if m.link_type and m.link_id else None),
        "link_id": m.link_id,
        "link_display": m.link_display,
    }


def _plain_presented_form(a) -> dict:
    return {
        "id": a.id,
        "content_type": a.content_type,
        "language": a.language,
        "data": a.data,
        "url": a.url,
        "size": a.size,
        "hash": a.hash,
        "title": a.title,
        "creation": a.creation.isoformat() if a.creation else None,
    }


def to_plain_diagnostic_report(dr: DiagnosticReportModel) -> dict:
    result = {
        "id": dr.diagnostic_report_id,
        "extension": list(dr.extension) if dr.extension else None,
        "identifier": [
            {**(_plain_identifier(i) or {}), "id": i.id} for i in (dr.identifiers or [])
        ]
        or None,
        "based_on": [_plain_reference_row(b, b.id) for b in (dr.based_ons or [])] or None,
        "status": fhir_enum(dr.status).replace("_", "-") if dr.status else None,
        "category": [
            {**(_plain_codeable_concept(c.codings, c.text) or {}), "id": c.id} for c in (dr.categories or [])
        ]
        or None,
        "code_codings": [
            {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "user_selected": c.user_selected,
            }
            for c in (dr.code_codings or [])
        ]
        or None,
        "code_text": dr.code_text,
        "subject": _plain_reference(dr, "subject"),
        "encounter": _plain_reference(dr, "encounter"),
        "effective_date_time": dr.effective_date_time.isoformat() if dr.effective_date_time else None,
        "effective_period_start": dr.effective_period_start.isoformat() if dr.effective_period_start else None,
        "effective_period_end": dr.effective_period_end.isoformat() if dr.effective_period_end else None,
        "issued": dr.issued.isoformat() if dr.issued else None,
        "performer": [_plain_reference_row(p, p.id) for p in (dr.performers or [])] or None,
        "results_interpreter": [_plain_reference_row(r, r.id) for r in (dr.results_interpreters or [])] or None,
        "specimen": [_plain_reference_row(s, s.id) for s in (dr.specimens or [])] or None,
        "result": [_plain_reference_row(r, r.id) for r in (dr.results or [])] or None,
        "imaging_study": [_plain_reference_row(i, i.id) for i in (dr.imaging_studies or [])] or None,
        "media": [_plain_media(m) for m in (dr.media or [])] or None,
        "conclusion": dr.conclusion,
        "conclusion_code": [
            {**(_plain_codeable_concept(c.codings, c.text) or {}), "id": c.id} for c in (dr.conclusion_codes or [])
        ]
        or None,
        "presented_form": [_plain_presented_form(a) for a in (dr.presented_forms or [])] or None,
        "org_id": dr.tenant_id,
        "created_at": dr.created_at.isoformat() if dr.created_at else None,
        "updated_at": dr.updated_at.isoformat() if dr.updated_at else None,
        "created_by": dr.created_by,
        "updated_by": dr.updated_by,
    }
    return {k: v for k, v in result.items() if v is not None}
