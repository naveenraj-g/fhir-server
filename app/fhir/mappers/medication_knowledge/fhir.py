from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.medication_knowledge import (
        MedicationKnowledgeAdminGuideline,
        MedicationKnowledgeCost,
        MedicationKnowledgeDrugCharacteristic,
        MedicationKnowledgeIngredient,
        MedicationKnowledgeKinetics,
        MedicationKnowledgeMedicineClassification,
        MedicationKnowledgeModel,
        MedicationKnowledgeMonitoringProgram,
        MedicationKnowledgeMonograph,
        MedicationKnowledgeRegulatory,
        MedicationKnowledgeRelated,
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
            id_type: dict = {}
            if type_coding:
                id_type["coding"] = [type_coding]
            if id_type_text:
                id_type["text"] = id_type_text
            if id_type:
                identifier["type"] = id_type
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
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
            identifier["period"] = p
        entry["identifier"] = identifier

    return entry or None


def _fhir_quantity(obj, prefix: str) -> dict | None:
    val_attr = f"{prefix}_value" if prefix else "value"
    cmp_attr = f"{prefix}_comparator" if prefix else "comparator"
    unit_attr = f"{prefix}_unit" if prefix else "unit"
    sys_attr = f"{prefix}_system" if prefix else "system"
    code_attr = f"{prefix}_code" if prefix else "code"

    val = getattr(obj, val_attr, None)
    comparator = getattr(obj, cmp_attr, None)
    unit = getattr(obj, unit_attr, None)
    system = getattr(obj, sys_attr, None)
    code = getattr(obj, code_attr, None)

    if val is None and comparator is None and not unit and not system and not code:
        return None
    res: dict = {}
    if val is not None:
        res["value"] = float(val)
    if comparator is not None:
        res["comparator"] = fhir_enum(comparator)
    if unit:
        res["unit"] = unit
    if system:
        res["system"] = system
    if code:
        res["code"] = code
    return res


def _fhir_ratio(obj, prefix: str) -> dict | None:
    num = _fhir_quantity(obj, f"{prefix}_numerator")
    denom = _fhir_quantity(obj, f"{prefix}_denominator")
    if not num and not denom:
        return None
    res: dict = {}
    if num:
        res["numerator"] = num
    if denom:
        res["denominator"] = denom
    return res


def _fhir_money(obj, prefix: str) -> dict | None:
    val = getattr(obj, f"{prefix}_value", None)
    currency = getattr(obj, f"{prefix}_currency", None)
    if val is None and not currency:
        return None
    res: dict = {}
    if val is not None:
        res["value"] = float(val)
    if currency:
        res["currency"] = currency
    return res


def fhir_medication_knowledge_packaging(m: MedicationKnowledgeModel) -> dict | None:
    pkg_type = _fhir_codeable_concept(m.packaging_type_codings, m.packaging_type_text)
    pkg_qty = _fhir_quantity(m, "packaging_quantity")
    if not pkg_type and not pkg_qty:
        return None
    res: dict = {}
    if pkg_type:
        res["type"] = pkg_type
    if pkg_qty:
        res["quantity"] = pkg_qty
    return res


def fhir_medication_knowledge_related(r: MedicationKnowledgeRelated) -> dict:
    res: dict = {}
    type_cc = _fhir_codeable_concept(r.type_codings, r.type_text)
    if type_cc:
        res["type"] = type_cc
    refs = [
        _fhir_reference_with_identifier_fallback(ref, "reference")
        for ref in (r.references or [])
    ]
    refs = [ref for ref in refs if ref is not None]
    if refs:
        res["reference"] = refs
    return res


def fhir_medication_knowledge_monograph(mono: MedicationKnowledgeMonograph) -> dict:
    res: dict = {}
    type_cc = _fhir_codeable_concept(mono.type_codings, mono.type_text)
    if type_cc:
        res["type"] = type_cc
    source = _fhir_reference_with_identifier_fallback(mono, "source")
    if source:
        res["source"] = source
    return res


def fhir_medication_knowledge_ingredient(ing: MedicationKnowledgeIngredient) -> dict:
    res: dict = {}
    item_cc = _fhir_codeable_concept(ing.item_codings, ing.item_codeable_concept_text)
    if item_cc:
        res["itemCodeableConcept"] = item_cc
    item_ref = _fhir_reference_with_identifier_fallback(ing, "item")
    if item_ref:
        res["itemReference"] = item_ref
    if ing.is_active is not None:
        res["isActive"] = ing.is_active
    strength = _fhir_ratio(ing, "strength")
    if strength:
        res["strength"] = strength
    return res


def fhir_medication_knowledge_cost(c: MedicationKnowledgeCost) -> dict:
    res: dict = {}
    type_cc = _fhir_codeable_concept(c.type_codings, c.type_text)
    if type_cc:
        res["type"] = type_cc
    if c.source:
        res["source"] = c.source
    cost_val = _fhir_money(c, "cost")
    if cost_val:
        res["cost"] = cost_val
    return res


def fhir_medication_knowledge_monitoring_program(mp: MedicationKnowledgeMonitoringProgram) -> dict:
    res: dict = {}
    type_cc = _fhir_codeable_concept(mp.type_codings, mp.type_text)
    if type_cc:
        res["type"] = type_cc
    if mp.name:
        res["name"] = mp.name
    return res


def fhir_medication_knowledge_admin_guideline(ag: MedicationKnowledgeAdminGuideline) -> dict:
    res: dict = {}
    dosages = []
    for d in ag.dosages or []:
        d_entry: dict = {}
        t_cc = _fhir_codeable_concept(d.type_codings, d.type_text)
        if t_cc:
            d_entry["type"] = t_cc
        if d.dosage:
            d_entry["dosage"] = d.dosage
        if d_entry:
            dosages.append(d_entry)
    if dosages:
        res["dosage"] = dosages

    ind_cc = _fhir_codeable_concept(ag.indication_codings, ag.indication_codeable_concept_text)
    if ind_cc:
        res["indicationCodeableConcept"] = ind_cc
    ind_ref = _fhir_reference_with_identifier_fallback(ag, "indication")
    if ind_ref:
        res["indicationReference"] = ind_ref

    chars = []
    for pc in ag.patient_characteristics or []:
        pc_entry: dict = {}
        c_cc = _fhir_codeable_concept(pc.characteristic_codings, pc.characteristic_codeable_concept_text)
        if c_cc:
            pc_entry["characteristicCodeableConcept"] = c_cc
        c_qty = _fhir_quantity(pc, "characteristic_quantity")
        if c_qty:
            pc_entry["characteristicQuantity"] = c_qty
        if pc.value:
            pc_entry["value"] = list(pc.value)
        if pc_entry:
            chars.append(pc_entry)
    if chars:
        res["patientCharacteristics"] = chars

    return res


def fhir_medication_knowledge_medicine_classification(
    mc: MedicationKnowledgeMedicineClassification,
) -> dict:
    res: dict = {}
    type_cc = _fhir_codeable_concept(mc.type_codings, mc.type_text)
    if type_cc:
        res["type"] = type_cc
    items = []
    for item in mc.classification_items or []:
        item_cc = _fhir_codeable_concept(item.codings, item.text)
        if item_cc:
            items.append(item_cc)
    if items:
        res["classification"] = items
    return res


def fhir_medication_knowledge_drug_characteristic(
    dc: MedicationKnowledgeDrugCharacteristic,
) -> dict:
    res: dict = {}
    type_cc = _fhir_codeable_concept(dc.type_codings, dc.type_text)
    if type_cc:
        res["type"] = type_cc
    v_cc = _fhir_codeable_concept(dc.value_codings, dc.value_codeable_concept_text)
    if v_cc:
        res["valueCodeableConcept"] = v_cc
    if dc.value_string:
        res["valueString"] = dc.value_string
    v_qty = _fhir_quantity(dc, "value_quantity")
    if v_qty:
        res["valueQuantity"] = v_qty
    if dc.value_base64_binary:
        res["valueBase64Binary"] = dc.value_base64_binary
    return res


def fhir_medication_knowledge_regulatory(reg: MedicationKnowledgeRegulatory) -> dict:
    res: dict = {}
    auth = _fhir_reference_with_identifier_fallback(reg, "regulatory_authority")
    if auth:
        res["regulatoryAuthority"] = auth

    subs = []
    for s in reg.substitutions or []:
        s_entry: dict = {}
        s_cc = _fhir_codeable_concept(s.type_codings, s.type_text)
        if s_cc:
            s_entry["type"] = s_cc
        if s.allowed is not None:
            s_entry["allowed"] = s.allowed
        if s_entry:
            subs.append(s_entry)
    if subs:
        res["substitution"] = subs

    scheds = []
    for sc in reg.schedules or []:
        sc_cc = _fhir_codeable_concept(sc.schedule_codings, sc.schedule_text)
        if sc_cc:
            scheds.append({"schedule": sc_cc})
    if scheds:
        res["schedule"] = scheds

    max_disp_qty = _fhir_quantity(reg, "max_dispense_quantity")
    max_disp_period = _fhir_quantity(reg, "max_dispense_period")
    if max_disp_qty or max_disp_period:
        md: dict = {}
        if max_disp_qty:
            md["quantity"] = max_disp_qty
        if max_disp_period:
            md["period"] = max_disp_period
        res["maxDispense"] = md

    return res


def fhir_medication_knowledge_kinetics(k: MedicationKnowledgeKinetics) -> dict:
    res: dict = {}
    aucs = []
    for a in k.area_under_curve or []:
        q = _fhir_quantity(a, "")
        if q:
            aucs.append(q)
    if aucs:
        res["areaUnderCurve"] = aucs

    ld50s = []
    for l in k.lethal_dose_50 or []:
        q = _fhir_quantity(l, "")
        if q:
            ld50s.append(q)
    if ld50s:
        res["lethalDose50"] = ld50s

    hlp = _fhir_quantity(k, "half_life_period")
    if hlp:
        res["halfLifePeriod"] = hlp

    return res


def _fhir_meta(model: MedicationKnowledgeModel) -> dict:
    return {"lastUpdated": fhir_instant(model.updated_at or model.created_at)}


def to_fhir_medication_knowledge(m: MedicationKnowledgeModel) -> dict:
    """Format a MedicationKnowledgeModel as a FHIR R4 JSON dict."""
    res = {
        "resourceType": "MedicationKnowledge",
        "id": str(m.medication_knowledge_id),
        "meta": _fhir_meta(m),
        "extension": list(m.extension) if m.extension else None,
        "code": _fhir_codeable_concept(m.code_codings, m.code_text),
        "status": fhir_enum(m.status) if m.status else None,
        "manufacturer": _fhir_reference_with_identifier_fallback(m, "manufacturer"),
        "doseForm": _fhir_codeable_concept(m.dose_form_codings, m.dose_form_text),
        "amount": _fhir_quantity(m, "amount"),
        "synonym": list(m.synonym) if m.synonym else None,
        "relatedMedicationKnowledge": [
            fhir_medication_knowledge_related(r) for r in (m.related_knowledge or [])
        ]
        or None,
        "associatedMedication": [
            _fhir_reference_with_identifier_fallback(a, "reference")
            for a in (m.associated_medications or [])
        ]
        or None,
        "productType": [
            _fhir_codeable_concept(pt.codings, pt.text)
            for pt in (m.product_types or [])
        ]
        or None,
        "monograph": [
            fhir_medication_knowledge_monograph(mono) for mono in (m.monographs or [])
        ]
        or None,
        "ingredient": [
            fhir_medication_knowledge_ingredient(ing) for ing in (m.ingredients or [])
        ]
        or None,
        "preparationInstruction": m.preparation_instruction,
        "intendedRoute": [
            _fhir_codeable_concept(ir.codings, ir.text)
            for ir in (m.intended_routes or [])
        ]
        or None,
        "cost": [fhir_medication_knowledge_cost(c) for c in (m.costs or [])] or None,
        "monitoringProgram": [
            fhir_medication_knowledge_monitoring_program(mp)
            for mp in (m.monitoring_programs or [])
        ]
        or None,
        "administrationGuidelines": [
            fhir_medication_knowledge_admin_guideline(ag)
            for ag in (m.administration_guidelines or [])
        ]
        or None,
        "medicineClassification": [
            fhir_medication_knowledge_medicine_classification(mc)
            for mc in (m.medicine_classifications or [])
        ]
        or None,
        "packaging": fhir_medication_knowledge_packaging(m),
        "drugCharacteristic": [
            fhir_medication_knowledge_drug_characteristic(dc)
            for dc in (m.drug_characteristics or [])
        ]
        or None,
        "contraindication": [
            _fhir_reference_with_identifier_fallback(c, "reference")
            for c in (m.contraindications or [])
        ]
        or None,
        "regulatory": [
            fhir_medication_knowledge_regulatory(reg) for reg in (m.regulatory or [])
        ]
        or None,
        "kinetics": [
            fhir_medication_knowledge_kinetics(k) for k in (m.kinetics or [])
        ]
        or None,
    }
    return {k: v for k, v in res.items() if v is not None}
