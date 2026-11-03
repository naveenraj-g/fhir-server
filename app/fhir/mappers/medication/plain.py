from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.medication import (
        MedicationIdentifier,
        MedicationIngredient,
        MedicationModel,
    )


def _plain_coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            k: v
            for k, v in {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "user_selected": c.user_selected,
            }.items()
            if v is not None
        }
        if entry:
            result.append(entry)
    return result


def _plain_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _plain_coding_list(codings)
    result: dict = {}
    if text:
        result["text"] = text
    if coding_list:
        result["coding"] = coding_list
    return result or None


def _plain_reference(obj, prefix: str) -> dict | None:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    if not raw_reference and not (ref_type and ref_id) and not display:
        return None

    res: dict = {
        "reference": raw_reference or (f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None),
        "type": fhir_enum(ref_type) if ref_type else None,
        "id": ref_id,
        "display": display,
    }

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    if id_use is not None:
        res["identifier_use"] = fhir_enum(id_use)
    for col in (
        "identifier_type_system",
        "identifier_type_version",
        "identifier_type_code",
        "identifier_type_display",
        "identifier_type_user_selected",
        "identifier_type_text",
        "identifier_system",
        "identifier_value",
        "identifier_period_start",
        "identifier_period_end",
    ):
        v = getattr(obj, f"{prefix}_{col}", None)
        if v is not None:
            res[col] = v

    return {k: v for k, v in res.items() if v is not None}


def _plain_quantity(prefix: str, obj) -> dict | None:
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


def _plain_ratio(prefix: str, obj) -> dict | None:
    num = _plain_quantity(f"{prefix}_numerator", obj)
    den = _plain_quantity(f"{prefix}_denominator", obj)
    if not num and not den:
        return None
    res: dict = {}
    if num:
        res["numerator"] = num
    if den:
        res["denominator"] = den
    return res


def plain_medication_identifier(i: MedicationIdentifier) -> dict:
    entry: dict = {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type": _plain_codeable_concept(i.type_codings, i.type_text),
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start,
        "period_end": i.period_end,
    }
    assigner = _plain_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return {k: v for k, v in entry.items() if v is not None}


def plain_medication_ingredient(ing: MedicationIngredient) -> dict:
    entry: dict = {
        "id": ing.id,
        "item_codeable_concept": _plain_codeable_concept(
            ing.item_codings, ing.item_codeable_concept_text
        ),
        "item_reference": _plain_reference(ing, "item"),
        "is_active": ing.is_active,
        "strength": _plain_ratio("strength", ing),
    }
    return {k: v for k, v in entry.items() if v is not None}


def _plain_batch(m: MedicationModel) -> dict | None:
    lot = m.batch_lot_number
    exp = m.batch_expiration_date
    if not lot and not exp:
        return None
    res: dict = {}
    if lot:
        res["lot_number"] = lot
    if exp:
        res["expiration_date"] = exp
    return res


def to_plain_medication(m: MedicationModel) -> dict:
    """Format a MedicationModel as a plain snake_case dict."""
    res = {
        "id": m.medication_id,
        "extension": list(m.extension) if m.extension else None,
        "identifier": [
            plain_medication_identifier(i) for i in (m.identifiers or [])
        ]
        or None,
        "code": _plain_codeable_concept(m.code_codings, m.code_text),
        "status": fhir_enum(m.status) if m.status else None,
        "manufacturer": _plain_reference(m, "manufacturer"),
        "form": _plain_codeable_concept(m.form_codings, m.form_text),
        "amount": _plain_ratio("amount", m),
        "ingredient": [
            plain_medication_ingredient(ing) for ing in (m.ingredients or [])
        ]
        or None,
        "batch": _plain_batch(m),
    }
    return {k: v for k, v in res.items() if v is not None}
