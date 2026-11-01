from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.flag import (
        FlagCategory,
        FlagIdentifier,
        FlagModel,
    )

_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


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


def _fhir_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_reference(obj, prefix: str) -> dict | None:
    if obj is None:
        return None
    ref = getattr(obj, f"{prefix}_reference", None)
    rtype = getattr(obj, f"{prefix}_type", None)
    rid = getattr(obj, f"{prefix}_id", None)
    disp = getattr(obj, f"{prefix}_display", None)

    out: dict[str, Any] = {}
    if ref:
        out["reference"] = ref
    elif rtype and rid:
        type_str = fhir_enum(rtype)
        out["reference"] = f"{type_str}/{rid}"
    if disp:
        out["display"] = disp

    use = getattr(obj, f"{prefix}_identifier_use", None)
    val = getattr(obj, f"{prefix}_identifier_value", None)
    sys = getattr(obj, f"{prefix}_identifier_system", None)
    type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    p_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    p_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if (
        use
        or val
        or sys
        or type_code
        or p_start
        or p_end
        or getattr(obj, f"{prefix}_identifier_type_text", None)
    ):
        ident: dict[str, Any] = {}
        if use:
            ident["use"] = fhir_enum(use)
        if sys:
            ident["system"] = sys
        if val:
            ident["value"] = val
        if type_code or getattr(obj, f"{prefix}_identifier_type_text", None):
            coding: dict[str, Any] = {}
            if getattr(obj, f"{prefix}_identifier_type_system", None):
                coding["system"] = getattr(obj, f"{prefix}_identifier_type_system")
            if getattr(obj, f"{prefix}_identifier_type_version", None):
                coding["version"] = getattr(obj, f"{prefix}_identifier_type_version")
            if type_code:
                coding["code"] = type_code
            if getattr(obj, f"{prefix}_identifier_type_display", None):
                coding["display"] = getattr(obj, f"{prefix}_identifier_type_display")
            if getattr(obj, f"{prefix}_identifier_type_user_selected", None) is not None:
                coding["userSelected"] = getattr(obj, f"{prefix}_identifier_type_user_selected")

            type_dict: dict[str, Any] = {}
            if coding:
                type_dict["coding"] = [coding]
            if getattr(obj, f"{prefix}_identifier_type_text", None):
                type_dict["text"] = getattr(obj, f"{prefix}_identifier_type_text")
            if type_dict:
                ident["type"] = type_dict
        if p_start or p_end:
            period: dict[str, Any] = {}
            if p_start:
                period["start"] = fhir_instant(p_start)
            if p_end:
                period["end"] = fhir_instant(p_end)
            ident["period"] = period
        out["identifier"] = ident

    return out or None


def _fhir_identifier(i: FlagIdentifier) -> dict | None:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = _fhir_codeable_concept(getattr(i, "type_codings", None), i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        period: dict = {}
        if i.period_start:
            period["start"] = fhir_instant(i.period_start)
        if i.period_end:
            period["end"] = fhir_instant(i.period_end)
        entry["period"] = period
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_category(cat: FlagCategory) -> dict | None:
    return _fhir_codeable_concept(getattr(cat, "codings", None), cat.text)


def _fhir_meta(model: FlagModel) -> dict:
    meta: dict = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    exts: list[dict] = []
    if model.tenant_id:
        exts.append({"url": f"{_EXT_BASE}/tenant-id", "valueString": model.tenant_id})
    if model.created_by:
        exts.append({"url": f"{_EXT_BASE}/created-by", "valueString": model.created_by})
    if model.updated_by:
        exts.append({"url": f"{_EXT_BASE}/updated-by", "valueString": model.updated_by})
    if model.created_at:
        exts.append({"url": f"{_EXT_BASE}/created-at", "valueInstant": fhir_instant(model.created_at)})
    if exts:
        meta["extension"] = exts
    return meta


def to_fhir_flag(model: FlagModel) -> dict:
    """Serialize a FlagModel ORM instance to a FHIR R4 Flag dict."""
    result: dict[str, Any] = {
        "resourceType": "Flag",
        "id": str(model.flag_id),
    }

    meta = _fhir_meta(model)
    if meta:
        result["meta"] = meta

    if model.extension:
        result["extension"] = list(model.extension)

    identifiers = [
        item
        for item in (_fhir_identifier(i) for i in (model.identifiers or []))
        if item is not None
    ]
    if identifiers:
        result["identifier"] = identifiers

    result["status"] = fhir_enum(model.status)

    categories = [
        item
        for item in (_fhir_category(c) for c in (model.categories or []))
        if item is not None
    ]
    if categories:
        result["category"] = categories

    code = _fhir_codeable_concept(model.code_codings, model.code_text)
    if code:
        result["code"] = code

    subject = _fhir_reference(model, "subject")
    if subject:
        result["subject"] = subject

    if model.period_start or model.period_end:
        period: dict = {}
        if model.period_start:
            period["start"] = fhir_instant(model.period_start)
        if model.period_end:
            period["end"] = fhir_instant(model.period_end)
        result["period"] = period

    encounter = _fhir_reference(model, "encounter")
    if encounter:
        result["encounter"] = encounter

    author = _fhir_reference(model, "author")
    if author:
        result["author"] = author

    return {k: v for k, v in result.items() if v is not None}
