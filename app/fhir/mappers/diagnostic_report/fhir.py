from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.diagnostic_report import DiagnosticReportModel


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


def _fhir_reference(obj, prefix: str) -> dict:
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
    return entry


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict:
    entry = _fhir_reference(obj, prefix)

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_type_user_selected = getattr(obj, f"{prefix}_identifier_type_user_selected", None)
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
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
            identifier["period"] = {
                k: v
                for k, v in {"start": fhir_instant(id_period_start), "end": fhir_instant(id_period_end)}.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def fhir_diagnostic_report_identifier(obj, prefix: str = "") -> dict:
    """Renders a full DiagnosticReportIdentifier child row into a FHIR
    Identifier dict."""
    p = prefix
    entry: dict = {}
    use = getattr(obj, f"{p}use", None)
    if use:
        entry["use"] = fhir_enum(use)
    codings_attr = f"{p}type_codings" if p else "type_codings"
    coding = _fhir_coding_list(getattr(obj, codings_attr, None))
    type_text = getattr(obj, f"{p}type_text", None)
    if coding or type_text:
        type_cc: dict = {}
        if coding:
            type_cc["coding"] = coding
        if type_text:
            type_cc["text"] = type_text
        entry["type"] = type_cc
    system = getattr(obj, f"{p}system", None)
    if system:
        entry["system"] = system
    value = getattr(obj, f"{p}value", None)
    if value:
        entry["value"] = value
    period_start = getattr(obj, f"{p}period_start", None)
    period_end = getattr(obj, f"{p}period_end", None)
    if period_start or period_end:
        entry["period"] = {
            k: v for k, v in {"start": fhir_instant(period_start), "end": fhir_instant(period_end)}.items() if v
        }
    assigner = _fhir_reference_with_identifier_fallback(obj, f"{p}assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_diagnostic_report_codeable_concept(codings, text: str | None) -> dict:
    """Generic CodeableConcept renderer — reused for every plain {coding[],
    text} field on this resource."""
    entry: dict = {}
    coding = _fhir_coding_list(codings)
    if coding:
        entry["coding"] = coding
    if text:
        entry["text"] = text
    return entry


def fhir_diagnostic_report_media(m) -> dict:
    entry: dict = {}
    if m.comment:
        entry["comment"] = m.comment
    link = _fhir_reference_with_identifier_fallback(m, "link")
    if link:
        entry["link"] = link
    return entry


def fhir_diagnostic_report_presented_form(a) -> dict:
    return {
        k: v
        for k, v in {
            "contentType": a.content_type,
            "language": a.language,
            "data": a.data,
            "url": a.url,
            "size": a.size,
            "hash": a.hash,
            "title": a.title,
            "creation": fhir_instant(a.creation) if a.creation else None,
        }.items()
        if v is not None
    }


_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(dr: DiagnosticReportModel) -> dict:
    meta: dict = {}
    if dr.updated_at:
        meta["lastUpdated"] = fhir_instant(dr.updated_at)
    extensions = []
    if dr.tenant_id:
        extensions.append({"url": f"{_EXT_BASE}/org-id", "valueString": dr.tenant_id})
    if dr.created_by:
        extensions.append({"url": f"{_EXT_BASE}/created-by", "valueString": dr.created_by})
    if dr.updated_by:
        extensions.append({"url": f"{_EXT_BASE}/updated-by", "valueString": dr.updated_by})
    if dr.created_at:
        extensions.append({"url": f"{_EXT_BASE}/created-at", "valueDateTime": fhir_instant(dr.created_at)})
    if extensions:
        meta["extension"] = extensions
    return meta


def to_fhir_diagnostic_report(dr: DiagnosticReportModel) -> dict:
    result: dict = {"resourceType": "DiagnosticReport", "id": str(dr.diagnostic_report_id)}

    meta = _fhir_meta(dr)
    if meta:
        result["meta"] = meta
    if dr.extension:
        result["extension"] = list(dr.extension)

    identifiers = [fhir_diagnostic_report_identifier(i) for i in (dr.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    based_ons = [_fhir_reference_with_identifier_fallback(b, "reference") for b in (dr.based_ons or [])]
    based_ons = [b for b in based_ons if b]
    if based_ons:
        result["basedOn"] = based_ons

    if dr.status:
        result["status"] = fhir_enum(dr.status).replace("_", "-")

    categories = [fhir_diagnostic_report_codeable_concept(c.codings, c.text) for c in (dr.categories or [])]
    categories = [c for c in categories if c]
    if categories:
        result["category"] = categories

    result["code"] = fhir_diagnostic_report_codeable_concept(dr.code_codings, dr.code_text)

    subject = _fhir_reference_with_identifier_fallback(dr, "subject")
    if subject:
        result["subject"] = subject

    encounter = _fhir_reference_with_identifier_fallback(dr, "encounter")
    if encounter:
        result["encounter"] = encounter

    if dr.effective_date_time:
        result["effectiveDateTime"] = fhir_instant(dr.effective_date_time)
    elif dr.effective_period_start or dr.effective_period_end:
        result["effectivePeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(dr.effective_period_start),
                "end": fhir_instant(dr.effective_period_end),
            }.items()
            if v
        }

    if dr.issued:
        result["issued"] = fhir_instant(dr.issued)

    performers = [_fhir_reference_with_identifier_fallback(p, "reference") for p in (dr.performers or [])]
    performers = [p for p in performers if p]
    if performers:
        result["performer"] = performers

    results_interpreters = [
        _fhir_reference_with_identifier_fallback(r, "reference") for r in (dr.results_interpreters or [])
    ]
    results_interpreters = [r for r in results_interpreters if r]
    if results_interpreters:
        result["resultsInterpreter"] = results_interpreters

    specimens = [_fhir_reference_with_identifier_fallback(s, "reference") for s in (dr.specimens or [])]
    specimens = [s for s in specimens if s]
    if specimens:
        result["specimen"] = specimens

    results = [_fhir_reference_with_identifier_fallback(r, "reference") for r in (dr.results or [])]
    results = [r for r in results if r]
    if results:
        result["result"] = results

    imaging_studies = [_fhir_reference_with_identifier_fallback(i, "reference") for i in (dr.imaging_studies or [])]
    imaging_studies = [i for i in imaging_studies if i]
    if imaging_studies:
        result["imagingStudy"] = imaging_studies

    media = [fhir_diagnostic_report_media(m) for m in (dr.media or [])]
    media = [m for m in media if m]
    if media:
        result["media"] = media

    if dr.conclusion:
        result["conclusion"] = dr.conclusion

    conclusion_codes = [
        fhir_diagnostic_report_codeable_concept(c.codings, c.text) for c in (dr.conclusion_codes or [])
    ]
    conclusion_codes = [c for c in conclusion_codes if c]
    if conclusion_codes:
        result["conclusionCode"] = conclusion_codes

    presented_forms = [fhir_diagnostic_report_presented_form(a) for a in (dr.presented_forms or [])]
    presented_forms = [a for a in presented_forms if a]
    if presented_forms:
        result["presentedForm"] = presented_forms

    return {k: v for k, v in result.items() if v is not None}
