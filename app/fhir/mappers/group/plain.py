from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.group import (
        GroupCharacteristic,
        GroupIdentifier,
        GroupMember,
        GroupModel,
    )


def _plain_ref(ref_raw: str | None, ref_type: Any, ref_id: int | None) -> str | None:
    if ref_raw:
        return ref_raw
    if ref_type and ref_id:
        return f"{fhir_enum(ref_type)}/{ref_id}"
    return None


def _plain_codeable_concept(codings, text: str | None) -> dict | None:
    c_list = [
        {
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
        }
        for c in codings or []
    ]
    if not c_list and not text:
        return None
    res: dict = {}
    if text:
        res["text"] = text
    if c_list:
        res["coding"] = c_list
    return res


def _plain_identifier(i: GroupIdentifier) -> dict:
    return {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type": _plain_codeable_concept(getattr(i, "type_codings", None), i.type_text),
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start,
        "period_end": i.period_end,
        "assigner": _plain_ref(i.assigner_reference, i.assigner_type, i.assigner_id),
        "assigner_display": i.assigner_display,
    }


def _plain_characteristic(c: GroupCharacteristic) -> dict:
    return {
        "id": c.id,
        "code": _plain_codeable_concept(getattr(c, "code_codings", None), c.code_text),
        "exclude": c.exclude,
        "period_start": c.period_start,
        "period_end": c.period_end,
        "value_boolean": c.value_boolean,
        "value_codeable_concept": _plain_codeable_concept(
            getattr(c, "value_codeable_concept_codings", None),
            c.value_codeable_concept_text,
        ),
        "value_quantity": c.value_quantity,
        "value_range": c.value_range,
        "value_reference": _plain_ref(
            c.value_reference_reference,
            c.value_reference_type,
            c.value_reference_id,
        ),
        "value_reference_display": c.value_reference_display,
    }


def _plain_member(m: GroupMember) -> dict:
    return {
        "id": m.id,
        "entity": _plain_ref(m.entity_reference, m.entity_type, m.entity_id),
        "entity_display": m.entity_display,
        "period_start": m.period_start,
        "period_end": m.period_end,
        "inactive": m.inactive,
    }


def to_plain_group(model: GroupModel) -> dict:
    """Map GroupModel to plain snake_case dict."""
    res: dict[str, Any] = {
        "id": model.group_id,
        "active": model.active,
        "type": fhir_enum(model.type),
        "actual": model.actual,
        "code": _plain_codeable_concept(
            getattr(model, "code_codings", None),
            model.code_text,
        ),
        "name": model.name,
        "quantity": model.quantity,
        "managing_entity": _plain_ref(
            model.managing_entity_reference,
            model.managing_entity_type,
            model.managing_entity_id,
        ),
        "managing_entity_display": model.managing_entity_display,
        "identifier": (
            [_plain_identifier(i) for i in model.identifiers]
            if getattr(model, "identifiers", None)
            else None
        ),
        "characteristic": (
            [_plain_characteristic(c) for c in model.characteristics]
            if getattr(model, "characteristics", None)
            else None
        ),
        "member": (
            [_plain_member(m) for m in model.members]
            if getattr(model, "members", None)
            else None
        ),
        "extension": model.extension if model.extension else None,
    }
    return res
