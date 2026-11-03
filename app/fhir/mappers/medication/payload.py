"""Payload -> FHIR JSON conversion for Medication.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(MedicationCreateSchema / MedicationPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.medication.input import (
        MedicationBatchInput,
        MedicationCodeableConceptInput,
        MedicationCreateSchema,
        MedicationIdentifierInput,
        MedicationIngredientInput,
        MedicationPatchSchema,
        MedicationQuantityInput,
        MedicationRatioInput,
    )

_MANUFACTURER_FIELDS = {
    "manufacturer",
    "manufacturer_display",
    "manufacturer_identifier_use",
    "manufacturer_identifier_type_system",
    "manufacturer_identifier_type_version",
    "manufacturer_identifier_type_code",
    "manufacturer_identifier_type_display",
    "manufacturer_identifier_type_user_selected",
    "manufacturer_identifier_type_text",
    "manufacturer_identifier_system",
    "manufacturer_identifier_value",
    "manufacturer_identifier_period_start",
    "manufacturer_identifier_period_end",
}
_MANUFACTURER_FHIR_KEYS = {"manufacturer"}


def _val(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _payload_coding_list(codings: list | None) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            k: v
            for k, v in {
                "system": _val(c, "system"),
                "version": _val(c, "version"),
                "code": _val(c, "code"),
                "display": _val(c, "display"),
                "userSelected": _val(c, "user_selected"),
            }.items()
            if v is not None
        }
        if entry:
            result.append(entry)
    return result


def payload_medication_codeable_concept(
    cc: MedicationCodeableConceptInput | dict | None,
) -> dict | None:
    if not cc:
        return None
    coding_list = _payload_coding_list(_val(cc, "coding"))
    text = _val(cc, "text")
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _reference_with_prefix_from_payload(obj: Any, prefix: str) -> dict | None:
    if not obj:
        return None
    ref = _val(obj, prefix) or _val(obj, f"{prefix}_reference")
    display = _val(obj, f"{prefix}_display")

    id_use = _val(obj, f"{prefix}_identifier_use")
    id_type_system = _val(obj, f"{prefix}_identifier_type_system")
    id_type_version = _val(obj, f"{prefix}_identifier_type_version")
    id_type_code = _val(obj, f"{prefix}_identifier_type_code")
    id_type_display = _val(obj, f"{prefix}_identifier_type_display")
    id_type_user_selected = _val(obj, f"{prefix}_identifier_type_user_selected")
    id_type_text = _val(obj, f"{prefix}_identifier_type_text")
    id_system = _val(obj, f"{prefix}_identifier_system")
    id_value = _val(obj, f"{prefix}_identifier_value")
    id_period_start = _val(obj, f"{prefix}_identifier_period_start")
    id_period_end = _val(obj, f"{prefix}_identifier_period_end")

    entry: dict = {}
    if ref:
        entry["reference"] = ref
    if display:
        entry["display"] = display

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
            identifier["use"] = id_use.value if hasattr(id_use, "value") else str(id_use)
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


def _payload_quantity(q: MedicationQuantityInput | dict | None) -> dict | None:
    if not q:
        return None
    val = _val(q, "value")
    comp = _val(q, "comparator")
    unit = _val(q, "unit")
    sys = _val(q, "system")
    code = _val(q, "code")

    if val is None and comp is None and unit is None and sys is None and code is None:
        return None

    entry: dict = {}
    if val is not None:
        entry["value"] = float(val)
    if comp is not None:
        entry["comparator"] = comp.value if hasattr(comp, "value") else str(comp)
    if unit is not None:
        entry["unit"] = unit
    if sys is not None:
        entry["system"] = sys
    if code is not None:
        entry["code"] = code
    return entry


def _payload_ratio(r: MedicationRatioInput | dict | None) -> dict | None:
    if not r:
        return None
    num = _payload_quantity(_val(r, "numerator"))
    den = _payload_quantity(_val(r, "denominator"))
    if not num and not den:
        return None
    res: dict = {}
    if num:
        res["numerator"] = num
    if den:
        res["denominator"] = den
    return res


def payload_medication_identifier(i: MedicationIdentifierInput) -> dict:
    entry: dict = {}
    use = _val(i, "use")
    if use:
        entry["use"] = use.value if hasattr(use, "value") else str(use)
    type_cc = payload_medication_codeable_concept(_val(i, "type"))
    if type_cc:
        entry["type"] = type_cc
    sys = _val(i, "system")
    if sys:
        entry["system"] = sys
    val = _val(i, "value")
    if val:
        entry["value"] = val
    start = _val(i, "period_start")
    end = _val(i, "period_end")
    if start or end:
        period: dict = {}
        if start:
            period["start"] = start.isoformat() if hasattr(start, "isoformat") else str(start)
        if end:
            period["end"] = end.isoformat() if hasattr(end, "isoformat") else str(end)
        entry["period"] = period
    assigner = _reference_with_prefix_from_payload(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def payload_medication_ingredient(ing: MedicationIngredientInput) -> dict:
    entry: dict = {}
    item_cc = payload_medication_codeable_concept(_val(ing, "item_codeable_concept"))
    if item_cc:
        entry["itemCodeableConcept"] = item_cc
    item_ref = _reference_with_prefix_from_payload(ing, "item")
    if item_ref:
        entry["itemReference"] = item_ref
    is_act = _val(ing, "is_active")
    if is_act is not None:
        entry["isActive"] = is_act
    strength = _payload_ratio(_val(ing, "strength"))
    if strength:
        entry["strength"] = strength
    return entry


def _payload_batch(b: MedicationBatchInput | dict | None) -> dict | None:
    if not b:
        return None
    lot = _val(b, "lot_number")
    exp = _val(b, "expiration_date")
    if not lot and not exp:
        return None
    res: dict = {}
    if lot:
        res["lotNumber"] = lot
    if exp:
        res["expirationDate"] = exp.isoformat() if hasattr(exp, "isoformat") else str(exp)
    return res


def payload_to_fhir_medication(payload: MedicationCreateSchema) -> dict:
    """Format a validated MedicationCreateSchema as a FHIR R4 JSON dict."""
    out: dict = {
        "resourceType": "Medication",
    }

    if payload.extension:
        out["extension"] = list(payload.extension)

    identifiers = [
        payload_medication_identifier(i)
        for i in (payload.identifier or [])
    ]
    if identifiers:
        out["identifier"] = identifiers

    code = payload_medication_codeable_concept(payload.code)
    if code:
        out["code"] = code

    if payload.status:
        out["status"] = (
            payload.status.value
            if hasattr(payload.status, "value")
            else str(payload.status)
        )

    manufacturer = _reference_with_prefix_from_payload(payload, "manufacturer")
    if manufacturer:
        out["manufacturer"] = manufacturer

    form = payload_medication_codeable_concept(payload.form)
    if form:
        out["form"] = form

    amount = _payload_ratio(payload.amount)
    if amount:
        out["amount"] = amount

    ingredients = [
        payload_medication_ingredient(ing)
        for ing in (payload.ingredient or [])
    ]
    if ingredients:
        out["ingredient"] = ingredients

    batch = _payload_batch(payload.batch)
    if batch:
        out["batch"] = batch

    return out


def patch_fragment_to_fhir_medication(
    patch: MedicationPatchSchema,
) -> tuple[dict, set[str]]:
    """Build a partial FHIR fragment containing ONLY fields present in patch.model_fields_set."""
    fragment: dict = {}
    touched: set[str] = set()
    fields_set = patch.model_fields_set

    if "extension" in fields_set:
        touched.add("extension")
        if patch.extension is not None:
            fragment["extension"] = list(patch.extension)

    if "identifier" in fields_set:
        touched.add("identifier")
        if patch.identifier is not None:
            fragment["identifier"] = [
                payload_medication_identifier(i) for i in patch.identifier
            ]

    if "code" in fields_set:
        touched.add("code")
        if patch.code is not None:
            c = payload_medication_codeable_concept(patch.code)
            if c:
                fragment["code"] = c

    if "status" in fields_set:
        touched.add("status")
        if patch.status is not None:
            fragment["status"] = (
                patch.status.value
                if hasattr(patch.status, "value")
                else str(patch.status)
            )

    if fields_set & _MANUFACTURER_FIELDS:
        touched.update(_MANUFACTURER_FHIR_KEYS)
        m = _reference_with_prefix_from_payload(patch, "manufacturer")
        if m:
            fragment["manufacturer"] = m

    if "form" in fields_set:
        touched.add("form")
        if patch.form is not None:
            f = payload_medication_codeable_concept(patch.form)
            if f:
                fragment["form"] = f

    if "amount" in fields_set:
        touched.add("amount")
        if patch.amount is not None:
            a = _payload_ratio(patch.amount)
            if a:
                fragment["amount"] = a

    if "ingredient" in fields_set:
        touched.add("ingredient")
        if patch.ingredient is not None:
            fragment["ingredient"] = [
                payload_medication_ingredient(ing) for ing in patch.ingredient
            ]

    if "batch" in fields_set:
        touched.add("batch")
        if patch.batch is not None:
            b = _payload_batch(patch.batch)
            if b:
                fragment["batch"] = b

    return fragment, touched


__all__ = [
    "payload_to_fhir_medication",
    "patch_fragment_to_fhir_medication",
    "merge_patch_fragment",
]
