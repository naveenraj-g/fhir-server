"""Payload -> FHIR JSON conversion for MedicationKnowledge.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(MedicationKnowledgeCreateSchema / MedicationKnowledgePatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.medication_knowledge.input import (
        MedicationKnowledgeAdminGuidelineInput,
        MedicationKnowledgeCodeableConceptInput,
        MedicationKnowledgeCostInput,
        MedicationKnowledgeCreateSchema,
        MedicationKnowledgeDrugCharacteristicInput,
        MedicationKnowledgeIngredientInput,
        MedicationKnowledgeKineticsInput,
        MedicationKnowledgeMedicineClassificationInput,
        MedicationKnowledgeMoneyInput,
        MedicationKnowledgeMonitoringProgramInput,
        MedicationKnowledgeMonographInput,
        MedicationKnowledgePackagingInput,
        MedicationKnowledgePatchSchema,
        MedicationKnowledgeQuantityInput,
        MedicationKnowledgeRatioInput,
        MedicationKnowledgeRegulatoryInput,
        MedicationKnowledgeRelatedInput,
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


def payload_medication_knowledge_codeable_concept(
    cc: MedicationKnowledgeCodeableConceptInput | dict | None,
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

    res: dict = {}
    if ref:
        res["reference"] = ref
    if display:
        res["display"] = display

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
        ident: dict = {}
        if id_use:
            ident["use"] = id_use.value if hasattr(id_use, "value") else str(id_use)
        type_coding: dict = {}
        if id_type_system:
            type_coding["system"] = id_type_system
        if id_type_version:
            type_coding["version"] = id_type_version
        if id_type_code:
            type_coding["code"] = id_type_code
        if id_type_display:
            type_coding["display"] = id_type_display
        if id_type_user_selected is not None:
            type_coding["userSelected"] = id_type_user_selected
        type_dict: dict = {}
        if type_coding:
            type_dict["coding"] = [type_coding]
        if id_type_text:
            type_dict["text"] = id_type_text
        if type_dict:
            ident["type"] = type_dict
        if id_system:
            ident["system"] = id_system
        if id_value:
            ident["value"] = id_value
        if id_period_start or id_period_end:
            p: dict = {}
            if id_period_start:
                p["start"] = (
                    id_period_start.isoformat()
                    if hasattr(id_period_start, "isoformat")
                    else str(id_period_start)
                )
            if id_period_end:
                p["end"] = (
                    id_period_end.isoformat()
                    if hasattr(id_period_end, "isoformat")
                    else str(id_period_end)
                )
            ident["period"] = p
        res["identifier"] = ident

    return res or None


def _payload_quantity(q: MedicationKnowledgeQuantityInput | dict | None) -> dict | None:
    if not q:
        return None
    val = _val(q, "value")
    cmp_val = _val(q, "comparator")
    unit = _val(q, "unit")
    system = _val(q, "system")
    code = _val(q, "code")

    if val is None and cmp_val is None and not unit and not system and not code:
        return None
    res: dict = {}
    if val is not None:
        res["value"] = float(val)
    if cmp_val is not None:
        res["comparator"] = (
            cmp_val.value if hasattr(cmp_val, "value") else str(cmp_val)
        )
    if unit:
        res["unit"] = unit
    if system:
        res["system"] = system
    if code:
        res["code"] = code
    return res


def _payload_ratio(r: MedicationKnowledgeRatioInput | dict | None) -> dict | None:
    if not r:
        return None
    num = _payload_quantity(_val(r, "numerator"))
    denom = _payload_quantity(_val(r, "denominator"))
    if not num and not denom:
        return None
    res: dict = {}
    if num:
        res["numerator"] = num
    if denom:
        res["denominator"] = denom
    return res


def _payload_money(m: MedicationKnowledgeMoneyInput | dict | None) -> dict | None:
    if not m:
        return None
    val = _val(m, "value")
    cur = _val(m, "currency")
    if val is None and not cur:
        return None
    res: dict = {}
    if val is not None:
        res["value"] = float(val)
    if cur:
        res["currency"] = cur
    return res


def payload_medication_knowledge_packaging(
    pkg: MedicationKnowledgePackagingInput | dict | None,
) -> dict | None:
    if not pkg:
        return None
    pkg_type = payload_medication_knowledge_codeable_concept(_val(pkg, "type"))
    pkg_qty = _payload_quantity(_val(pkg, "quantity"))
    if not pkg_type and not pkg_qty:
        return None
    res: dict = {}
    if pkg_type:
        res["type"] = pkg_type
    if pkg_qty:
        res["quantity"] = pkg_qty
    return res


def payload_medication_knowledge_related(
    r: MedicationKnowledgeRelatedInput | dict | None,
) -> dict | None:
    if not r:
        return None
    res: dict = {}
    type_cc = payload_medication_knowledge_codeable_concept(_val(r, "type"))
    if type_cc:
        res["type"] = type_cc
    refs = _val(r, "reference")
    if refs:
        res["reference"] = [{"reference": ref} for ref in refs]
    return res or None


def payload_medication_knowledge_monograph(
    mono: MedicationKnowledgeMonographInput | dict | None,
) -> dict | None:
    if not mono:
        return None
    res: dict = {}
    type_cc = payload_medication_knowledge_codeable_concept(_val(mono, "type"))
    if type_cc:
        res["type"] = type_cc
    source = _reference_with_prefix_from_payload(mono, "source")
    if source:
        res["source"] = source
    return res or None


def payload_medication_knowledge_ingredient(
    ing: MedicationKnowledgeIngredientInput | dict | None,
) -> dict | None:
    if not ing:
        return None
    res: dict = {}
    item_cc = payload_medication_knowledge_codeable_concept(
        _val(ing, "item_codeable_concept")
    )
    if item_cc:
        res["itemCodeableConcept"] = item_cc
    item_ref = _reference_with_prefix_from_payload(ing, "item")
    if item_ref:
        res["itemReference"] = item_ref
    is_active = _val(ing, "is_active")
    if is_active is not None:
        res["isActive"] = is_active
    strength = _payload_ratio(_val(ing, "strength"))
    if strength:
        res["strength"] = strength
    return res or None


def payload_medication_knowledge_cost(
    c: MedicationKnowledgeCostInput | dict | None,
) -> dict | None:
    if not c:
        return None
    res: dict = {}
    type_cc = payload_medication_knowledge_codeable_concept(_val(c, "type"))
    if type_cc:
        res["type"] = type_cc
    src = _val(c, "source")
    if src:
        res["source"] = src
    cost_val = _payload_money(_val(c, "cost"))
    if cost_val:
        res["cost"] = cost_val
    return res or None


def payload_medication_knowledge_monitoring_program(
    mp: MedicationKnowledgeMonitoringProgramInput | dict | None,
) -> dict | None:
    if not mp:
        return None
    res: dict = {}
    type_cc = payload_medication_knowledge_codeable_concept(_val(mp, "type"))
    if type_cc:
        res["type"] = type_cc
    name = _val(mp, "name")
    if name:
        res["name"] = name
    return res or None


def payload_medication_knowledge_admin_guideline(
    ag: MedicationKnowledgeAdminGuidelineInput | dict | None,
) -> dict | None:
    if not ag:
        return None
    res: dict = {}
    dosages = []
    for d in _val(ag, "dosage") or []:
        d_entry: dict = {}
        t_cc = payload_medication_knowledge_codeable_concept(_val(d, "type"))
        if t_cc:
            d_entry["type"] = t_cc
        dosage_list = _val(d, "dosage")
        if dosage_list:
            d_entry["dosage"] = dosage_list
        if d_entry:
            dosages.append(d_entry)
    if dosages:
        res["dosage"] = dosages

    ind_cc = payload_medication_knowledge_codeable_concept(
        _val(ag, "indication_codeable_concept")
    )
    if ind_cc:
        res["indicationCodeableConcept"] = ind_cc
    ind_ref = _reference_with_prefix_from_payload(ag, "indication")
    if ind_ref:
        res["indicationReference"] = ind_ref

    chars = []
    for pc in _val(ag, "patient_characteristics") or []:
        pc_entry: dict = {}
        c_cc = payload_medication_knowledge_codeable_concept(
            _val(pc, "characteristic_codeable_concept")
        )
        if c_cc:
            pc_entry["characteristicCodeableConcept"] = c_cc
        c_qty = _payload_quantity(_val(pc, "characteristic_quantity"))
        if c_qty:
            pc_entry["characteristicQuantity"] = c_qty
        vals = _val(pc, "value")
        if vals:
            pc_entry["value"] = list(vals)
        if pc_entry:
            chars.append(pc_entry)
    if chars:
        res["patientCharacteristics"] = chars

    return res or None


def payload_medication_knowledge_medicine_classification(
    mc: MedicationKnowledgeMedicineClassificationInput | dict | None,
) -> dict | None:
    if not mc:
        return None
    res: dict = {}
    type_cc = payload_medication_knowledge_codeable_concept(_val(mc, "type"))
    if type_cc:
        res["type"] = type_cc
    items = []
    for item in _val(mc, "classification") or []:
        item_cc = payload_medication_knowledge_codeable_concept(item)
        if item_cc:
            items.append(item_cc)
    if items:
        res["classification"] = items
    return res or None


def payload_medication_knowledge_drug_characteristic(
    dc: MedicationKnowledgeDrugCharacteristicInput | dict | None,
) -> dict | None:
    if not dc:
        return None
    res: dict = {}
    type_cc = payload_medication_knowledge_codeable_concept(_val(dc, "type"))
    if type_cc:
        res["type"] = type_cc
    v_cc = payload_medication_knowledge_codeable_concept(
        _val(dc, "value_codeable_concept")
    )
    if v_cc:
        res["valueCodeableConcept"] = v_cc
    v_str = _val(dc, "value_string")
    if v_str:
        res["valueString"] = v_str
    v_qty = _payload_quantity(_val(dc, "value_quantity"))
    if v_qty:
        res["valueQuantity"] = v_qty
    v_bin = _val(dc, "value_base64_binary")
    if v_bin:
        res["valueBase64Binary"] = v_bin
    return res or None


def payload_medication_knowledge_regulatory(
    reg: MedicationKnowledgeRegulatoryInput | dict | None,
) -> dict | None:
    if not reg:
        return None
    res: dict = {}
    auth = _reference_with_prefix_from_payload(reg, "regulatory_authority")
    if auth:
        res["regulatoryAuthority"] = auth

    subs = []
    for s in _val(reg, "substitution") or []:
        s_entry: dict = {}
        s_cc = payload_medication_knowledge_codeable_concept(_val(s, "type"))
        if s_cc:
            s_entry["type"] = s_cc
        allowed = _val(s, "allowed")
        if allowed is not None:
            s_entry["allowed"] = allowed
        if s_entry:
            subs.append(s_entry)
    if subs:
        res["substitution"] = subs

    scheds = []
    for sc in _val(reg, "schedule") or []:
        sc_cc = payload_medication_knowledge_codeable_concept(_val(sc, "schedule"))
        if sc_cc:
            scheds.append({"schedule": sc_cc})
    if scheds:
        res["schedule"] = scheds

    md_input = _val(reg, "max_dispense")
    if md_input:
        max_disp_qty = _payload_quantity(_val(md_input, "quantity"))
        max_disp_period = _payload_quantity(_val(md_input, "period"))
        if max_disp_qty or max_disp_period:
            md: dict = {}
            if max_disp_qty:
                md["quantity"] = max_disp_qty
            if max_disp_period:
                md["period"] = max_disp_period
            res["maxDispense"] = md

    return res or None


def payload_medication_knowledge_kinetics(
    k: MedicationKnowledgeKineticsInput | dict | None,
) -> dict | None:
    if not k:
        return None
    res: dict = {}
    aucs = []
    for a in _val(k, "area_under_curve") or []:
        q = _payload_quantity(a)
        if q:
            aucs.append(q)
    if aucs:
        res["areaUnderCurve"] = aucs

    ld50s = []
    for l in _val(k, "lethal_dose_50") or []:
        q = _payload_quantity(l)
        if q:
            ld50s.append(q)
    if ld50s:
        res["lethalDose50"] = ld50s

    hlp = _payload_quantity(_val(k, "half_life_period"))
    if hlp:
        res["halfLifePeriod"] = hlp

    return res or None


def payload_to_fhir_medication_knowledge(
    payload: MedicationKnowledgeCreateSchema,
) -> dict:
    """Convert MedicationKnowledgeCreateSchema to a FHIR R4 JSON dict."""
    status_val = (
        payload.status.value
        if hasattr(payload.status, "value")
        else str(payload.status)
        if payload.status
        else None
    )

    res = {
        "resourceType": "MedicationKnowledge",
        "code": payload_medication_knowledge_codeable_concept(payload.code),
        "status": status_val,
        "manufacturer": _reference_with_prefix_from_payload(payload, "manufacturer"),
        "doseForm": payload_medication_knowledge_codeable_concept(payload.dose_form),
        "amount": _payload_quantity(payload.amount),
        "synonym": list(payload.synonym) if payload.synonym else None,
        "relatedMedicationKnowledge": [
            payload_medication_knowledge_related(r)
            for r in (payload.related_medication_knowledge or [])
        ]
        or None,
        "associatedMedication": [
            {"reference": a} for a in (payload.associated_medication or [])
        ]
        or None,
        "productType": [
            payload_medication_knowledge_codeable_concept(pt)
            for pt in (payload.product_type or [])
        ]
        or None,
        "monograph": [
            payload_medication_knowledge_monograph(mono)
            for mono in (payload.monograph or [])
        ]
        or None,
        "ingredient": [
            payload_medication_knowledge_ingredient(ing)
            for ing in (payload.ingredient or [])
        ]
        or None,
        "preparationInstruction": payload.preparation_instruction,
        "intendedRoute": [
            payload_medication_knowledge_codeable_concept(ir)
            for ir in (payload.intended_route or [])
        ]
        or None,
        "cost": [
            payload_medication_knowledge_cost(c) for c in (payload.cost or [])
        ]
        or None,
        "monitoringProgram": [
            payload_medication_knowledge_monitoring_program(mp)
            for mp in (payload.monitoring_program or [])
        ]
        or None,
        "administrationGuidelines": [
            payload_medication_knowledge_admin_guideline(ag)
            for ag in (payload.administration_guidelines or [])
        ]
        or None,
        "medicineClassification": [
            payload_medication_knowledge_medicine_classification(mc)
            for mc in (payload.medicine_classification or [])
        ]
        or None,
        "packaging": payload_medication_knowledge_packaging(payload.packaging),
        "drugCharacteristic": [
            payload_medication_knowledge_drug_characteristic(dc)
            for dc in (payload.drug_characteristic or [])
        ]
        or None,
        "contraindication": [
            {"reference": c} for c in (payload.contraindication or [])
        ]
        or None,
        "regulatory": [
            payload_medication_knowledge_regulatory(reg)
            for reg in (payload.regulatory or [])
        ]
        or None,
        "kinetics": [
            payload_medication_knowledge_kinetics(k)
            for k in (payload.kinetics or [])
        ]
        or None,
        "extension": list(payload.extension) if payload.extension else None,
    }
    return {k: v for k, v in res.items() if v is not None}


def patch_fragment_to_fhir_medication_knowledge(
    patch: MedicationKnowledgePatchSchema,
) -> tuple[dict, set[str]]:
    """Convert a MedicationKnowledgePatchSchema into a FHIR R4 fragment and touched fields set."""
    fields_set = patch.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "extension" in fields_set:
        touched.add("extension")
        if patch.extension is not None:
            fragment["extension"] = list(patch.extension)

    if "code" in fields_set:
        touched.add("code")
        if patch.code is not None:
            c = payload_medication_knowledge_codeable_concept(patch.code)
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

    if "dose_form" in fields_set:
        touched.add("doseForm")
        if patch.dose_form is not None:
            df = payload_medication_knowledge_codeable_concept(patch.dose_form)
            if df:
                fragment["doseForm"] = df

    if "amount" in fields_set:
        touched.add("amount")
        if patch.amount is not None:
            a = _payload_quantity(patch.amount)
            if a:
                fragment["amount"] = a

    if "synonym" in fields_set:
        touched.add("synonym")
        if patch.synonym is not None:
            fragment["synonym"] = list(patch.synonym)

    if "related_medication_knowledge" in fields_set:
        touched.add("relatedMedicationKnowledge")
        if patch.related_medication_knowledge is not None:
            fragment["relatedMedicationKnowledge"] = [
                payload_medication_knowledge_related(r)
                for r in patch.related_medication_knowledge
            ]

    if "associated_medication" in fields_set:
        touched.add("associatedMedication")
        if patch.associated_medication is not None:
            fragment["associatedMedication"] = [
                {"reference": a} for a in patch.associated_medication
            ]

    if "product_type" in fields_set:
        touched.add("productType")
        if patch.product_type is not None:
            fragment["productType"] = [
                payload_medication_knowledge_codeable_concept(pt)
                for pt in patch.product_type
            ]

    if "monograph" in fields_set:
        touched.add("monograph")
        if patch.monograph is not None:
            fragment["monograph"] = [
                payload_medication_knowledge_monograph(mono)
                for mono in patch.monograph
            ]

    if "ingredient" in fields_set:
        touched.add("ingredient")
        if patch.ingredient is not None:
            fragment["ingredient"] = [
                payload_medication_knowledge_ingredient(ing)
                for ing in patch.ingredient
            ]

    if "preparation_instruction" in fields_set:
        touched.add("preparationInstruction")
        if patch.preparation_instruction is not None:
            fragment["preparationInstruction"] = patch.preparation_instruction

    if "intended_route" in fields_set:
        touched.add("intendedRoute")
        if patch.intended_route is not None:
            fragment["intendedRoute"] = [
                payload_medication_knowledge_codeable_concept(ir)
                for ir in patch.intended_route
            ]

    if "cost" in fields_set:
        touched.add("cost")
        if patch.cost is not None:
            fragment["cost"] = [
                payload_medication_knowledge_cost(c) for c in patch.cost
            ]

    if "monitoring_program" in fields_set:
        touched.add("monitoringProgram")
        if patch.monitoring_program is not None:
            fragment["monitoringProgram"] = [
                payload_medication_knowledge_monitoring_program(mp)
                for mp in patch.monitoring_program
            ]

    if "administration_guidelines" in fields_set:
        touched.add("administrationGuidelines")
        if patch.administration_guidelines is not None:
            fragment["administrationGuidelines"] = [
                payload_medication_knowledge_admin_guideline(ag)
                for ag in patch.administration_guidelines
            ]

    if "medicine_classification" in fields_set:
        touched.add("medicineClassification")
        if patch.medicine_classification is not None:
            fragment["medicineClassification"] = [
                payload_medication_knowledge_medicine_classification(mc)
                for mc in patch.medicine_classification
            ]

    if "packaging" in fields_set:
        touched.add("packaging")
        if patch.packaging is not None:
            pkg = payload_medication_knowledge_packaging(patch.packaging)
            if pkg:
                fragment["packaging"] = pkg

    if "drug_characteristic" in fields_set:
        touched.add("drugCharacteristic")
        if patch.drug_characteristic is not None:
            fragment["drugCharacteristic"] = [
                payload_medication_knowledge_drug_characteristic(dc)
                for dc in patch.drug_characteristic
            ]

    if "contraindication" in fields_set:
        touched.add("contraindication")
        if patch.contraindication is not None:
            fragment["contraindication"] = [
                {"reference": c} for c in patch.contraindication
            ]

    if "regulatory" in fields_set:
        touched.add("regulatory")
        if patch.regulatory is not None:
            fragment["regulatory"] = [
                payload_medication_knowledge_regulatory(reg)
                for reg in patch.regulatory
            ]

    if "kinetics" in fields_set:
        touched.add("kinetics")
        if patch.kinetics is not None:
            fragment["kinetics"] = [
                payload_medication_knowledge_kinetics(k) for k in patch.kinetics
            ]

    return fragment, touched


__all__ = [
    "payload_to_fhir_medication_knowledge",
    "patch_fragment_to_fhir_medication_knowledge",
    "merge_patch_fragment",
]
