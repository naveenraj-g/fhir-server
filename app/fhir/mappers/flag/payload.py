"""Payload -> FHIR JSON conversion for Flag.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(FlagCreateSchema / FlagPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant, merge_patch_fragment
from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES

if TYPE_CHECKING:
    from app.schemas.flag.input import (
        FlagCategoryInput,
        FlagCreateSchema,
        FlagIdentifierInput,
        FlagPatchSchema,
    )

_SUBJECT_FIELDS = {"subject", "subject_display"} | {
    f"subject_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES
}
_ENCOUNTER_FIELDS = {"encounter", "encounter_display"} | {
    f"encounter_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES
}
_AUTHOR_FIELDS = {"author", "author_display"} | {
    f"author_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES
}
_PERIOD_FIELDS = {"period_start", "period_end"}
_CODE_FIELDS = {"code_coding", "code_text"}


def _coding_from_payload(c: Any) -> dict:
    if isinstance(c, dict):
        return {
            k: v
            for k, v in {
                "system": c.get("system"),
                "version": c.get("version"),
                "code": c.get("code"),
                "display": c.get("display"),
                "userSelected": c.get("user_selected") or c.get("userSelected"),
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


def _reference_from_payload(obj: Any, prefix: str) -> dict | None:
    if not obj:
        return None

    def _get(field):
        return obj.get(field) if isinstance(obj, dict) else getattr(obj, field, None)

    raw_reference = _get(prefix)
    display = _get(f"{prefix}_display")

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    if display:
        entry["display"] = display

    id_use = _get(f"{prefix}_identifier_use")
    id_type_system = _get(f"{prefix}_identifier_type_system")
    id_type_version = _get(f"{prefix}_identifier_type_version")
    id_type_code = _get(f"{prefix}_identifier_type_code")
    id_type_display = _get(f"{prefix}_identifier_type_display")
    id_type_text = _get(f"{prefix}_identifier_type_text")
    id_type_user_selected = _get(f"{prefix}_identifier_type_user_selected")
    id_system = _get(f"{prefix}_identifier_system")
    id_value = _get(f"{prefix}_identifier_value")
    id_period_start = _get(f"{prefix}_identifier_period_start")
    id_period_end = _get(f"{prefix}_identifier_period_end")

    if (
        id_use
        or id_type_system
        or id_type_code
        or id_type_text
        or id_system
        or id_value
        or id_period_start
        or id_period_end
    ):
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
                for k, v in {
                    "start": fhir_instant(id_period_start),
                    "end": fhir_instant(id_period_end),
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry or None


def _identifier_from_payload(i: FlagIdentifierInput | dict) -> dict | None:
    if isinstance(i, dict):
        entry: dict = {}
        if i.get("use"):
            entry["use"] = fhir_enum(i["use"])
        type_codings = [
            _coding_from_payload(c) for c in (i.get("type_coding") or [])
        ]
        type_cc: dict = {}
        if type_codings:
            type_cc["coding"] = type_codings
        if i.get("type_text"):
            type_cc["text"] = i["type_text"]
        if type_cc:
            entry["type"] = type_cc
        if i.get("system"):
            entry["system"] = i["system"]
        if i.get("value"):
            entry["value"] = i["value"]
        if i.get("period_start") or i.get("period_end"):
            period: dict = {}
            if i.get("period_start"):
                period["start"] = fhir_instant(i["period_start"])
            if i.get("period_end"):
                period["end"] = fhir_instant(i["period_end"])
            entry["period"] = period
        assigner = _reference_from_payload(i, "assigner")
        if assigner:
            entry["assigner"] = assigner
        return entry or None

    entry = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_codings = [
        _coding_from_payload(c) for c in (i.type_coding or [])
    ]
    type_cc = {}
    if type_codings:
        type_cc["coding"] = type_codings
    if i.type_text:
        type_cc["text"] = i.type_text
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        period = {}
        if i.period_start:
            period["start"] = fhir_instant(i.period_start)
        if i.period_end:
            period["end"] = fhir_instant(i.period_end)
        entry["period"] = period
    assigner = _reference_from_payload(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _category_from_payload(cat: FlagCategoryInput | dict) -> dict | None:
    if isinstance(cat, dict):
        codings = [_coding_from_payload(c) for c in (cat.get("coding") or [])]
        res: dict = {}
        if codings:
            res["coding"] = codings
        if cat.get("text"):
            res["text"] = cat["text"]
        return res or None
    codings = [_coding_from_payload(c) for c in (cat.coding or [])]
    res = {}
    if codings:
        res["coding"] = codings
    if cat.text:
        res["text"] = cat.text
    return res or None


def payload_to_fhir_flag(payload: FlagCreateSchema) -> dict:
    """Convert a validated FlagCreateSchema to a genuine FHIR R4 Flag resource dict."""
    result: dict[str, Any] = {
        "resourceType": "Flag",
    }

    if payload.identifier:
        identifiers = [
            item
            for item in (_identifier_from_payload(i) for i in payload.identifier)
            if item is not None
        ]
        if identifiers:
            result["identifier"] = identifiers

    if payload.status:
        result["status"] = fhir_enum(payload.status)

    if payload.category:
        categories = [
            item
            for item in (_category_from_payload(c) for c in payload.category)
            if item is not None
        ]
        if categories:
            result["category"] = categories

    code: dict = {}
    if payload.code_coding:
        codings = [_coding_from_payload(c) for c in payload.code_coding]
        if codings:
            code["coding"] = codings
    if payload.code_text:
        code["text"] = payload.code_text
    if code:
        result["code"] = code

    subject = _reference_from_payload(payload, "subject")
    if subject:
        result["subject"] = subject

    if payload.period_start or payload.period_end:
        period: dict = {}
        if payload.period_start:
            period["start"] = fhir_instant(payload.period_start)
        if payload.period_end:
            period["end"] = fhir_instant(payload.period_end)
        result["period"] = period

    encounter = _reference_from_payload(payload, "encounter")
    if encounter:
        result["encounter"] = encounter

    author = _reference_from_payload(payload, "author")
    if author:
        result["author"] = author

    return {k: v for k, v in result.items() if v is not None}


def patch_fragment_to_fhir_flag(
    payload: FlagPatchSchema,
) -> tuple[dict, set[str]]:
    """Convert a FlagPatchSchema to a partial FHIR dict and set of touched FHIR top-level keys."""
    fragment: dict[str, Any] = {}
    touched: set[str] = set()
    fields_set = payload.model_fields_set

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                item
                for item in (_identifier_from_payload(i) for i in payload.identifier)
                if item is not None
            ]

    if "status" in fields_set:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = fhir_enum(payload.status)

    if "category" in fields_set:
        touched.add("category")
        if payload.category is not None:
            fragment["category"] = [
                item
                for item in (_category_from_payload(c) for c in payload.category)
                if item is not None
            ]

    if _CODE_FIELDS & fields_set:
        touched.add("code")
        code: dict = {}
        if payload.code_coding is not None:
            code["coding"] = [_coding_from_payload(c) for c in payload.code_coding]
        if payload.code_text is not None:
            code["text"] = payload.code_text
        if code:
            fragment["code"] = code

    if _SUBJECT_FIELDS & fields_set:
        touched.add("subject")
        subject = _reference_from_payload(payload, "subject")
        if subject:
            fragment["subject"] = subject

    if _PERIOD_FIELDS & fields_set:
        touched.add("period")
        period: dict = {}
        if payload.period_start is not None:
            period["start"] = fhir_instant(payload.period_start)
        if payload.period_end is not None:
            period["end"] = fhir_instant(payload.period_end)
        if period:
            fragment["period"] = period

    if _ENCOUNTER_FIELDS & fields_set:
        touched.add("encounter")
        encounter = _reference_from_payload(payload, "encounter")
        if encounter:
            fragment["encounter"] = encounter

    if _AUTHOR_FIELDS & fields_set:
        touched.add("author")
        author = _reference_from_payload(payload, "author")
        if author:
            fragment["author"] = author

    return fragment, touched
