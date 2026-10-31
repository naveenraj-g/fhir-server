"""Payload -> FHIR JSON conversion for Flag.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(FlagCreateSchema / FlagPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant, merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.flag.input import (
        FlagCategoryInput,
        FlagCreateSchema,
        FlagIdentifierInput,
        FlagPatchSchema,
    )

_SUBJECT_FIELDS = {"subject", "subject_display"}
_ENCOUNTER_FIELDS = {"encounter", "encounter_display"}
_AUTHOR_FIELDS = {"author", "author_display"}
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
        if i.get("assigner") or i.get("assigner_display"):
            assigner: dict = {}
            if i.get("assigner"):
                assigner["reference"] = i["assigner"]
            if i.get("assigner_display"):
                assigner["display"] = i["assigner_display"]
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
    if i.assigner or i.assigner_display:
        assigner = {}
        if i.assigner:
            assigner["reference"] = i.assigner
        if i.assigner_display:
            assigner["display"] = i.assigner_display
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

    subject: dict = {}
    if payload.subject:
        subject["reference"] = payload.subject
    if payload.subject_display:
        subject["display"] = payload.subject_display
    if subject:
        result["subject"] = subject

    if payload.period_start or payload.period_end:
        period: dict = {}
        if payload.period_start:
            period["start"] = fhir_instant(payload.period_start)
        if payload.period_end:
            period["end"] = fhir_instant(payload.period_end)
        result["period"] = period

    if payload.encounter or payload.encounter_display:
        encounter: dict = {}
        if payload.encounter:
            encounter["reference"] = payload.encounter
        if payload.encounter_display:
            encounter["display"] = payload.encounter_display
        result["encounter"] = encounter

    if payload.author or payload.author_display:
        author: dict = {}
        if payload.author:
            author["reference"] = payload.author
        if payload.author_display:
            author["display"] = payload.author_display
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
        subject: dict = {}
        if payload.subject is not None:
            subject["reference"] = payload.subject
        if payload.subject_display is not None:
            subject["display"] = payload.subject_display
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
        encounter: dict = {}
        if payload.encounter is not None:
            encounter["reference"] = payload.encounter
        if payload.encounter_display is not None:
            encounter["display"] = payload.encounter_display
        if encounter:
            fragment["encounter"] = encounter

    if _AUTHOR_FIELDS & fields_set:
        touched.add("author")
        author: dict = {}
        if payload.author is not None:
            author["reference"] = payload.author
        if payload.author_display is not None:
            author["display"] = payload.author_display
        if author:
            fragment["author"] = author

    return fragment, touched
