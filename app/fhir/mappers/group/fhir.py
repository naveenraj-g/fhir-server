from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.group import (
        GroupCharacteristic,
        GroupIdentifier,
        GroupMember,
        GroupModel,
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


def _fhir_identifier(i: GroupIdentifier) -> dict | None:
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


def _fhir_characteristic(c: GroupCharacteristic) -> dict | None:
    entry: dict = {}
    code_cc = _fhir_codeable_concept(getattr(c, "code_codings", None), c.code_text)
    if code_cc:
        entry["code"] = code_cc

    # Choice value[x]
    if c.value_boolean is not None:
        entry["valueBoolean"] = c.value_boolean
    elif getattr(c, "value_codeable_concept_codings", None) or c.value_codeable_concept_text:
        val_cc = _fhir_codeable_concept(
            getattr(c, "value_codeable_concept_codings", None),
            c.value_codeable_concept_text,
        )
        if val_cc:
            entry["valueCodeableConcept"] = val_cc
    elif c.value_quantity:
        entry["valueQuantity"] = c.value_quantity
    elif c.value_range:
        entry["valueRange"] = c.value_range
    elif c.value_reference_reference or (c.value_reference_type and c.value_reference_id):
        val_ref = _fhir_ref(
            c.value_reference_reference,
            c.value_reference_type,
            c.value_reference_id,
            c.value_reference_display,
        )
        if val_ref:
            entry["valueReference"] = val_ref

    entry["exclude"] = c.exclude

    if c.period_start or c.period_end:
        period: dict = {}
        if c.period_start:
            period["start"] = fhir_instant(c.period_start)
        if c.period_end:
            period["end"] = fhir_instant(c.period_end)
        entry["period"] = period

    return entry or None


def _fhir_member(m: GroupMember) -> dict | None:
    entry: dict = {}
    entity = _fhir_ref(m.entity_reference, m.entity_type, m.entity_id, m.entity_display)
    if entity:
        entry["entity"] = entity
    if m.period_start or m.period_end:
        period: dict = {}
        if m.period_start:
            period["start"] = fhir_instant(m.period_start)
        if m.period_end:
            period["end"] = fhir_instant(m.period_end)
        entry["period"] = period
    if m.inactive is not None:
        entry["inactive"] = m.inactive
    return entry or None


def to_fhir_group(model: GroupModel) -> dict:
    """Map GroupModel to FHIR R4 Group dict."""
    res: dict[str, Any] = {
        "resourceType": "Group",
        "id": str(model.group_id),
        "type": fhir_enum(model.type),
        "actual": model.actual,
    }

    if model.updated_at:
        res["meta"] = {
            "versionId": "1",
            "lastUpdated": fhir_instant(model.updated_at),
        }

    if getattr(model, "identifiers", None):
        id_list = [_fhir_identifier(i) for i in model.identifiers]
        id_list = [i for i in id_list if i]
        if id_list:
            res["identifier"] = id_list

    if model.active is not None:
        res["active"] = model.active

    code = _fhir_codeable_concept(
        getattr(model, "code_codings", None),
        model.code_text,
    )
    if code:
        res["code"] = code

    if model.name:
        res["name"] = model.name

    if model.quantity is not None:
        res["quantity"] = model.quantity

    managing_entity = _fhir_ref(
        model.managing_entity_reference,
        model.managing_entity_type,
        model.managing_entity_id,
        model.managing_entity_display,
    )
    if managing_entity:
        res["managingEntity"] = managing_entity

    if getattr(model, "characteristics", None):
        char_list = [_fhir_characteristic(c) for c in model.characteristics]
        char_list = [c for c in char_list if c]
        if char_list:
            res["characteristic"] = char_list

    if getattr(model, "members", None):
        mem_list = [_fhir_member(m) for m in model.members]
        mem_list = [m for m in mem_list if m]
        if mem_list:
            res["member"] = mem_list

    if model.extension:
        res["extension"] = model.extension

    return {k: v for k, v in res.items() if v is not None}
