"""Payload -> FHIR JSON conversion for Group.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(GroupCreateSchema / GroupPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant, merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.group.input import (
        GroupCharacteristicInput,
        GroupCodeableConceptInput,
        GroupCreateSchema,
        GroupIdentifierInput,
        GroupMemberInput,
        GroupPatchSchema,
    )

_MANAGING_ENTITY_FIELDS = {"managing_entity", "managing_entity_display"}


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


def _codeable_concept_from_payload(
    concept: GroupCodeableConceptInput | dict | None,
) -> dict | None:
    if not concept:
        return None
    if isinstance(concept, dict):
        codings = [_coding_from_payload(c) for c in (concept.get("coding") or [])]
        codings = [c for c in codings if c]
        text = concept.get("text")
    else:
        codings = [_coding_from_payload(c) for c in (concept.coding or [])]
        codings = [c for c in codings if c]
        text = concept.text

    result: dict = {}
    if codings:
        result["coding"] = codings
    if text:
        result["text"] = text
    return result or None


def _identifier_from_payload(
    ident: GroupIdentifierInput | dict | None,
) -> dict | None:
    if not ident:
        return None
    entry: dict = {}
    if isinstance(ident, dict):
        use = ident.get("use")
        type_in = ident.get("type")
        system = ident.get("system")
        value = ident.get("value")
        p_start = ident.get("period_start")
        p_end = ident.get("period_end")
        assigner = ident.get("assigner")
        assigner_disp = ident.get("assigner_display")
    else:
        use = ident.use
        type_in = ident.type
        system = ident.system
        value = ident.value
        p_start = ident.period_start
        p_end = ident.period_end
        assigner = ident.assigner
        assigner_disp = ident.assigner_display

    if use:
        entry["use"] = fhir_enum(use)
    type_cc = _codeable_concept_from_payload(type_in)
    if type_cc:
        entry["type"] = type_cc
    if system:
        entry["system"] = system
    if value:
        entry["value"] = value
    if p_start or p_end:
        period: dict = {}
        if p_start:
            period["start"] = fhir_instant(p_start)
        if p_end:
            period["end"] = fhir_instant(p_end)
        entry["period"] = period
    if assigner:
        ref: dict = {"reference": assigner}
        if assigner_disp:
            ref["display"] = assigner_disp
        entry["assigner"] = ref
    return entry or None


def _characteristic_from_payload(
    char: GroupCharacteristicInput | dict | None,
) -> dict | None:
    if not char:
        return None
    entry: dict = {}
    if isinstance(char, dict):
        code_in = char.get("code")
        exclude = char.get("exclude", False)
        p_start = char.get("period_start")
        p_end = char.get("period_end")
        val_bool = char.get("value_boolean")
        val_cc = char.get("value_codeable_concept")
        val_qty = char.get("value_quantity")
        val_range = char.get("value_range")
        val_ref = char.get("value_reference")
        val_ref_disp = char.get("value_reference_display")
    else:
        code_in = char.code
        exclude = char.exclude
        p_start = char.period_start
        p_end = char.period_end
        val_bool = char.value_boolean
        val_cc = char.value_codeable_concept
        val_qty = char.value_quantity
        val_range = char.value_range
        val_ref = char.value_reference
        val_ref_disp = char.value_reference_display

    code_res = _codeable_concept_from_payload(code_in)
    if code_res:
        entry["code"] = code_res

    # Choice value[x]
    if val_bool is not None:
        entry["valueBoolean"] = val_bool
    elif val_cc:
        v_cc = _codeable_concept_from_payload(val_cc)
        if v_cc:
            entry["valueCodeableConcept"] = v_cc
    elif val_qty:
        entry["valueQuantity"] = val_qty
    elif val_range:
        entry["valueRange"] = val_range
    elif val_ref:
        ref_dict: dict = {"reference": val_ref}
        if val_ref_disp:
            ref_dict["display"] = val_ref_disp
        entry["valueReference"] = ref_dict

    entry["exclude"] = exclude

    if p_start or p_end:
        period: dict = {}
        if p_start:
            period["start"] = fhir_instant(p_start)
        if p_end:
            period["end"] = fhir_instant(p_end)
        entry["period"] = period

    return entry or None


def _member_from_payload(
    mem: GroupMemberInput | dict | None,
) -> dict | None:
    if not mem:
        return None
    entry: dict = {}
    if isinstance(mem, dict):
        entity = mem.get("entity")
        entity_disp = mem.get("entity_display")
        p_start = mem.get("period_start")
        p_end = mem.get("period_end")
        inactive = mem.get("inactive")
    else:
        entity = mem.entity
        entity_disp = mem.entity_display
        p_start = mem.period_start
        p_end = mem.period_end
        inactive = mem.inactive

    if entity:
        ref: dict = {"reference": entity}
        if entity_disp:
            ref["display"] = entity_disp
        entry["entity"] = ref
    if p_start or p_end:
        period: dict = {}
        if p_start:
            period["start"] = fhir_instant(p_start)
        if p_end:
            period["end"] = fhir_instant(p_end)
        entry["period"] = period
    if inactive is not None:
        entry["inactive"] = inactive
    return entry or None


def payload_to_fhir_group(payload: GroupCreateSchema) -> dict:
    """Convert GroupCreateSchema to FHIR R4 JSON dict for pre-write validation."""
    d: dict[str, Any] = {
        "resourceType": "Group",
        "type": fhir_enum(payload.type),
        "actual": payload.actual,
    }

    if payload.active is not None:
        d["active"] = payload.active

    if payload.code:
        c = _codeable_concept_from_payload(payload.code)
        if c:
            d["code"] = c

    if payload.name:
        d["name"] = payload.name

    if payload.quantity is not None:
        d["quantity"] = payload.quantity

    if payload.managing_entity:
        ref: dict = {"reference": payload.managing_entity}
        if payload.managing_entity_display:
            ref["display"] = payload.managing_entity_display
        d["managingEntity"] = ref

    if payload.identifier:
        ids = [_identifier_from_payload(i) for i in payload.identifier]
        ids = [i for i in ids if i]
        if ids:
            d["identifier"] = ids

    if payload.characteristic:
        chars = [_characteristic_from_payload(c) for c in payload.characteristic]
        chars = [c for c in chars if c]
        if chars:
            d["characteristic"] = chars

    if payload.member:
        mems = [_member_from_payload(m) for m in payload.member]
        mems = [m for m in mems if m]
        if mems:
            d["member"] = mems

    if payload.extension:
        d["extension"] = payload.extension

    return {k: v for k, v in d.items() if v is not None}


def patch_fragment_to_fhir_group(
    payload: GroupPatchSchema,
) -> tuple[dict[str, Any], set[str]]:
    """Convert GroupPatchSchema to partial FHIR JSON fragment + touched field names."""
    fields_set = payload.model_fields_set
    fragment: dict[str, Any] = {}
    touched: set[str] = set()

    if "active" in fields_set:
        touched.add("active")
        if payload.active is not None:
            fragment["active"] = payload.active

    if "type" in fields_set:
        touched.add("type")
        if payload.type is not None:
            fragment["type"] = fhir_enum(payload.type)

    if "actual" in fields_set:
        touched.add("actual")
        if payload.actual is not None:
            fragment["actual"] = payload.actual

    if "code" in fields_set:
        touched.add("code")
        if payload.code is not None:
            fragment["code"] = _codeable_concept_from_payload(payload.code)

    if "name" in fields_set:
        touched.add("name")
        if payload.name is not None:
            fragment["name"] = payload.name

    if "quantity" in fields_set:
        touched.add("quantity")
        if payload.quantity is not None:
            fragment["quantity"] = payload.quantity

    if _MANAGING_ENTITY_FIELDS & fields_set:
        touched.add("managingEntity")
        if payload.managing_entity is not None or payload.managing_entity_display is not None:
            ref: dict = {}
            if payload.managing_entity:
                ref["reference"] = payload.managing_entity
            if payload.managing_entity_display:
                ref["display"] = payload.managing_entity_display
            if ref:
                fragment["managingEntity"] = ref

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                i for i in [_identifier_from_payload(x) for x in payload.identifier] if i
            ]

    if "characteristic" in fields_set:
        touched.add("characteristic")
        if payload.characteristic is not None:
            fragment["characteristic"] = [
                c for c in [_characteristic_from_payload(x) for x in payload.characteristic] if c
            ]

    if "member" in fields_set:
        touched.add("member")
        if payload.member is not None:
            fragment["member"] = [
                m for m in [_member_from_payload(x) for x in payload.member] if m
            ]

    if "extension" in fields_set:
        touched.add("extension")
        if payload.extension is not None:
            fragment["extension"] = payload.extension

    return fragment, touched
