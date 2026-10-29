"""Payload -> FHIR JSON conversion, the mirror image of fhir.py — see that
module's docstring pattern (e.g. app.fhir.mappers.observation.payload) for
the full reasoning. Reads the validated Pydantic input schema
(DiagnosticReportCreateSchema / DiagnosticReportPatchSchema and their
nested sub-schemas) rather than the persisted ORM model, before anything
is written to the DB.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.diagnostic_report.input import (
        DiagnosticReportCreateSchema,
        DiagnosticReportIdentifierInput,
        DiagnosticReportMediaInput,
        DiagnosticReportPatchSchema,
        DiagnosticReportPresentedFormInput,
    )
    from app.schemas.diagnostic_report.input.codeable_concept import DiagnosticReportCodeableConceptInput


def _coding_list(codings) -> list[dict]:
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


def _period(start, end) -> dict | None:
    period = {
        k: v
        for k, v in {"start": start.isoformat() if start else None, "end": end.isoformat() if end else None}.items()
        if v
    }
    return period or None


def _reference_from_payload_prefixed(obj, prefix: str) -> dict:
    entry: dict = {}
    if getattr(obj, f"{prefix}reference", None):
        entry["reference"] = getattr(obj, f"{prefix}reference")
    if getattr(obj, f"{prefix}display", None):
        entry["display"] = getattr(obj, f"{prefix}display")
    return entry


def _reference_with_identifier_fallback_from_payload(obj, prefix: str = "") -> dict:
    entry = _reference_from_payload_prefixed(obj, prefix)
    id_use = getattr(obj, f"{prefix}identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}identifier_type_system", None)
    id_type_code = getattr(obj, f"{prefix}identifier_type_code", None)
    id_type_text = getattr(obj, f"{prefix}identifier_type_text", None)
    id_system = getattr(obj, f"{prefix}identifier_system", None)
    id_value = getattr(obj, f"{prefix}identifier_value", None)
    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
        identifier: dict = {}
        if id_use:
            identifier["use"] = id_use.value if hasattr(id_use, "value") else id_use
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
                type_cc["coding"] = [
                    {
                        k: v
                        for k, v in {
                            "system": id_type_system,
                            "version": getattr(obj, f"{prefix}identifier_type_version", None),
                            "code": id_type_code,
                            "display": getattr(obj, f"{prefix}identifier_type_display", None),
                            "userSelected": getattr(obj, f"{prefix}identifier_type_user_selected", None),
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
        period = _period(
            getattr(obj, f"{prefix}identifier_period_start", None),
            getattr(obj, f"{prefix}identifier_period_end", None),
        )
        if period:
            identifier["period"] = period
        entry["identifier"] = identifier
    return entry


def payload_diagnostic_report_identifier(i: DiagnosticReportIdentifierInput) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = i.use.value
    coding = _coding_list(i.type_coding)
    if coding or i.type_text:
        type_cc: dict = {}
        if coding:
            type_cc["coding"] = coding
        if i.type_text:
            type_cc["text"] = i.type_text
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    period = _period(i.period_start, i.period_end)
    if period:
        entry["period"] = period
    if i.assigner:
        assigner: dict = {"reference": i.assigner}
        if i.assigner_display:
            assigner["display"] = i.assigner_display
        entry["assigner"] = assigner
    return entry


def payload_diagnostic_report_codeable_concept(cc: DiagnosticReportCodeableConceptInput) -> dict:
    entry: dict = {}
    coding = _coding_list(cc.coding)
    if coding:
        entry["coding"] = coding
    if cc.text:
        entry["text"] = cc.text
    return entry


def payload_diagnostic_report_media(m: DiagnosticReportMediaInput) -> dict:
    entry: dict = {}
    if m.comment:
        entry["comment"] = m.comment
    link = _reference_with_identifier_fallback_from_payload(m, "link_")
    if link:
        entry["link"] = link
    return entry


def payload_diagnostic_report_presented_form(a: DiagnosticReportPresentedFormInput) -> dict:
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
            "creation": a.creation.isoformat() if a.creation else None,
        }.items()
        if v is not None
    }


# field -> (fhir key, builder) for every plain 0..* list on this resource.
_LIST_FIELDS = {
    "identifier": ("identifier", payload_diagnostic_report_identifier),
    "based_on": ("basedOn", _reference_with_identifier_fallback_from_payload),
    "category": ("category", payload_diagnostic_report_codeable_concept),
    "performer": ("performer", _reference_with_identifier_fallback_from_payload),
    "results_interpreter": ("resultsInterpreter", _reference_with_identifier_fallback_from_payload),
    "specimen": ("specimen", _reference_with_identifier_fallback_from_payload),
    "result": ("result", _reference_with_identifier_fallback_from_payload),
    "imaging_study": ("imagingStudy", _reference_with_identifier_fallback_from_payload),
    "media": ("media", payload_diagnostic_report_media),
    "conclusion_code": ("conclusionCode", payload_diagnostic_report_codeable_concept),
    "presented_form": ("presentedForm", payload_diagnostic_report_presented_form),
}

_SINGLE_REFERENCE_FIELDS = {
    "subject": "subject",
    "encounter": "encounter",
}

_EFFECTIVE_FIELDS = {"effective_date_time", "effective_period_start", "effective_period_end"}


def _effective_choice(payload) -> tuple[str, object] | None:
    if payload.effective_date_time:
        return "effectiveDateTime", payload.effective_date_time.isoformat()
    period = _period(payload.effective_period_start, payload.effective_period_end)
    if period:
        return "effectivePeriod", period
    return None


def payload_to_fhir_diagnostic_report(payload: DiagnosticReportCreateSchema) -> dict:
    """Full-resource conversion for CREATE: every field is considered present."""
    result: dict = {"resourceType": "DiagnosticReport"}

    if payload.extension:
        result["extension"] = list(payload.extension)

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        items = [i for i in items if i]
        if items:
            result[fhir_key] = items

    if payload.status:
        result["status"] = payload.status.value

    result["code"] = payload_diagnostic_report_codeable_concept(payload.code)

    for field, fhir_key in _SINGLE_REFERENCE_FIELDS.items():
        obj = getattr(payload, field, None)
        if obj:
            ref = _reference_with_identifier_fallback_from_payload(obj)
            if ref:
                result[fhir_key] = ref

    effective = _effective_choice(payload)
    if effective:
        result[effective[0]] = effective[1]

    if payload.issued:
        result["issued"] = payload.issued.isoformat()

    if payload.conclusion:
        result["conclusion"] = payload.conclusion

    return result


def patch_fragment_to_fhir_diagnostic_report(payload: DiagnosticReportPatchSchema) -> tuple[dict, set[str]]:
    """Tri-state conversion for PATCH."""
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = list(payload.extension)

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            items = [builder(item) for item in (getattr(payload, field, None) or [])]
            items = [i for i in items if i]
            if items:
                fragment[fhir_key] = items

    if "status" in provided:
        touched.add("status")
        if payload.status:
            fragment["status"] = payload.status.value

    if "code" in provided:
        touched.add("code")
        if payload.code:
            cc = payload_diagnostic_report_codeable_concept(payload.code)
            if cc:
                fragment["code"] = cc

    for field, fhir_key in _SINGLE_REFERENCE_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            obj = getattr(payload, field, None)
            if obj:
                ref = _reference_with_identifier_fallback_from_payload(obj)
                if ref:
                    fragment[fhir_key] = ref

    if provided & _EFFECTIVE_FIELDS:
        touched.update({"effectiveDateTime", "effectivePeriod"})
        effective = _effective_choice(payload)
        if effective:
            fragment[effective[0]] = effective[1]

    if "issued" in provided:
        touched.add("issued")
        if payload.issued:
            fragment["issued"] = payload.issued.isoformat()

    if "conclusion" in provided:
        touched.add("conclusion")
        if payload.conclusion:
            fragment["conclusion"] = payload.conclusion

    return fragment, touched
