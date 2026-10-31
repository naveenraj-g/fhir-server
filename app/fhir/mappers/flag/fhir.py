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


def _fhir_ref(
    ref_raw: str | None,
    ref_type: Any,
    ref_id: int | None,
    display: str | None,
) -> dict | None:
    result: dict = {}
    if ref_raw:
        result["reference"] = ref_raw
    elif ref_type and ref_id:
        result["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        result["display"] = display
    return result or None


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
    assigner = _fhir_ref(
        i.assigner_reference,
        i.assigner_type,
        i.assigner_id,
        i.assigner_display,
    )
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

    subject = _fhir_ref(
        model.subject_reference,
        model.subject_type,
        model.subject_id,
        model.subject_display,
    )
    if subject:
        result["subject"] = subject

    if model.period_start or model.period_end:
        period: dict = {}
        if model.period_start:
            period["start"] = fhir_instant(model.period_start)
        if model.period_end:
            period["end"] = fhir_instant(model.period_end)
        result["period"] = period

    encounter = _fhir_ref(
        model.encounter_reference,
        model.encounter_type,
        model.encounter_id,
        model.encounter_display,
    )
    if encounter:
        result["encounter"] = encounter

    author = _fhir_ref(
        model.author_reference,
        model.author_type,
        model.author_id,
        model.author_display,
    )
    if author:
        result["author"] = author

    return {k: v for k, v in result.items() if v is not None}
