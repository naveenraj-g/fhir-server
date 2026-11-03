from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.medication import (
        MedicationIdentifier,
        MedicationIngredient,
        MedicationModel,
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


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict | None:
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

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_user_selected = getattr(obj, f"{prefix}_identifier_type_user_selected", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if (
        id_use
        or id_type_system
        or id_type_version
        or id_type_code
        or id_type_display
        or id_type_user_selected
        or id_type_text
        or id_system
        or id_value
        or id_period_start
        or id_period_end
    ):
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if (
            id_type_system
            or id_type_code
            or id_type_text
            or id_type_display
            or id_type_version
            or id_type_user_selected
        ):
            type_coding: dict = {}
            if id_type_system:
                type_coding["system"] = id_type_system
            if id_type_code:
                type_coding["code"] = id_type_code
            if id_type_display:
                type_coding["display"] = id_type_display
            if id_type_version:
                type_coding["version"] = id_type_version
            if id_type_user_selected is not None:
                type_coding["userSelected"] = id_type_user_selected
            t: dict = {}
            if type_coding:
                t["coding"] = [type_coding]
            if id_type_text:
                t["text"] = id_type_text
            if t:
                identifier["type"] = t
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_period_start or id_period_end:
            period: dict = {}
            if id_period_start:
                period["start"] = (
                    id_period_start.isoformat()
                    if hasattr(id_period_start, "isoformat")
                    else str(id_period_start)
                )
            if id_period_end:
                period["end"] = (
                    id_period_end.isoformat()
                    if hasattr(id_period_end, "isoformat")
                    else str(id_period_end)
                )
            identifier["period"] = period
        entry["identifier"] = identifier

    return entry or None


def _fhir_quantity(prefix: str, obj) -> dict | None:
    val = getattr(obj, f"{prefix}_value", None)
    comp = getattr(obj, f"{prefix}_comparator", None)
    unit = getattr(obj, f"{prefix}_unit", None)
    sys = getattr(obj, f"{prefix}_system", None)
    code = getattr(obj, f"{prefix}_code", None)

    if val is None and comp is None and unit is None and sys is None and code is None:
        return None

    entry: dict = {}
    if val is not None:
        entry["value"] = float(val)
    if comp is not None:
        raw_comp = fhir_enum(comp)
        symbol_map = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}
        entry["comparator"] = symbol_map.get(raw_comp, raw_comp)
    if unit is not None:
        entry["unit"] = unit
    if sys is not None:
        entry["system"] = sys
    if code is not None:
        entry["code"] = code
    return entry


def _fhir_ratio(prefix: str, obj) -> dict | None:
    num = _fhir_quantity(f"{prefix}_numerator", obj)
    den = _fhir_quantity(f"{prefix}_denominator", obj)
    if not num and not den:
        return None
    res: dict = {}
    if num:
        res["numerator"] = num
    if den:
        res["denominator"] = den
    return res


def fhir_medication_identifier(i: MedicationIdentifier) -> dict:
    res: dict = {}
    if i.use:
        res["use"] = fhir_enum(i.use)
    type_cc = _fhir_codeable_concept(i.type_codings, i.type_text)
    if type_cc:
        res["type"] = type_cc
    if i.system:
        res["system"] = i.system
    if i.value:
        res["value"] = i.value
    if i.period_start or i.period_end:
        p: dict = {}
        if i.period_start:
            p["start"] = (
                i.period_start.isoformat()
                if hasattr(i.period_start, "isoformat")
                else str(i.period_start)
            )
        if i.period_end:
            p["end"] = (
                i.period_end.isoformat()
                if hasattr(i.period_end, "isoformat")
                else str(i.period_end)
            )
        res["period"] = p
    assigner = _fhir_reference_with_identifier_fallback(i, "assigner")
    if assigner:
        res["assigner"] = assigner
    return res


def fhir_medication_ingredient(ing: MedicationIngredient) -> dict:
    entry: dict = {}
    item_cc = _fhir_codeable_concept(ing.item_codings, ing.item_codeable_concept_text)
    if item_cc:
        entry["itemCodeableConcept"] = item_cc
    item_ref = _fhir_reference_with_identifier_fallback(ing, "item")
    if item_ref:
        entry["itemReference"] = item_ref
    if ing.is_active is not None:
        entry["isActive"] = ing.is_active
    strength = _fhir_ratio("strength", ing)
    if strength:
        entry["strength"] = strength
    return entry


def _fhir_batch(m: MedicationModel) -> dict | None:
    lot = m.batch_lot_number
    exp = m.batch_expiration_date
    if not lot and not exp:
        return None
    res: dict = {}
    if lot:
        res["lotNumber"] = lot
    if exp:
        res["expirationDate"] = (
            exp.isoformat() if hasattr(exp, "isoformat") else str(exp)
        )
    return res


def _fhir_meta(model: MedicationModel) -> dict:
    return {"lastUpdated": fhir_instant(model.updated_at or model.created_at)}


def to_fhir_medication(m: MedicationModel) -> dict:
    """Format a MedicationModel as a FHIR R4 JSON dict."""
    res = {
        "resourceType": "Medication",
        "id": str(m.medication_id),
        "meta": _fhir_meta(m),
        "extension": list(m.extension) if m.extension else None,
        "identifier": [
            fhir_medication_identifier(i) for i in (m.identifiers or [])
        ]
        or None,
        "code": _fhir_codeable_concept(m.code_codings, m.code_text),
        "status": fhir_enum(m.status) if m.status else None,
        "manufacturer": _fhir_reference_with_identifier_fallback(m, "manufacturer"),
        "form": _fhir_codeable_concept(m.form_codings, m.form_text),
        "amount": _fhir_ratio("amount", m),
        "ingredient": [
            fhir_medication_ingredient(ing) for ing in (m.ingredients or [])
        ]
        or None,
        "batch": _fhir_batch(m),
    }
    return {k: v for k, v in res.items() if v is not None}
