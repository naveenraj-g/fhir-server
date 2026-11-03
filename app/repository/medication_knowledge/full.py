from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete
from sqlalchemy.future import select

from app.models.medication_knowledge import (
    MedicationKnowledgeAdminGuideline,
    MedicationKnowledgeAdminGuidelineDosage,
    MedicationKnowledgeAdminGuidelineDosageTypeCoding,
    MedicationKnowledgeAdminGuidelineIndicationCoding,
    MedicationKnowledgeAdminGuidelineIndicationReferenceType,
    MedicationKnowledgeAdminGuidelinePatientCharCoding,
    MedicationKnowledgeAdminGuidelinePatientCharacteristic,
    MedicationKnowledgeAssociatedMedication,
    MedicationKnowledgeAssociatedMedicationReferenceType,
    MedicationKnowledgeCodeCoding,
    MedicationKnowledgeContraindication,
    MedicationKnowledgeContraindicationReferenceType,
    MedicationKnowledgeCost,
    MedicationKnowledgeCostTypeCoding,
    MedicationKnowledgeDoseFormCoding,
    MedicationKnowledgeDrugCharacteristic,
    MedicationKnowledgeDrugCharacteristicTypeCoding,
    MedicationKnowledgeDrugCharacteristicValueCoding,
    MedicationKnowledgeIngredient,
    MedicationKnowledgeIngredientItemCoding,
    MedicationKnowledgeIngredientItemReferenceType,
    MedicationKnowledgeIntendedRoute,
    MedicationKnowledgeIntendedRouteCoding,
    MedicationKnowledgeKinetics,
    MedicationKnowledgeKineticsAreaUnderCurve,
    MedicationKnowledgeKineticsLethalDose50,
    MedicationKnowledgeManufacturerReferenceType,
    MedicationKnowledgeMedicineClassification,
    MedicationKnowledgeMedicineClassificationItem,
    MedicationKnowledgeMedicineClassificationItemCoding,
    MedicationKnowledgeMedicineClassificationTypeCoding,
    MedicationKnowledgeModel,
    MedicationKnowledgeMonitoringProgram,
    MedicationKnowledgeMonitoringProgramTypeCoding,
    MedicationKnowledgeMonograph,
    MedicationKnowledgeMonographSourceReferenceType,
    MedicationKnowledgeMonographTypeCoding,
    MedicationKnowledgePackagingTypeCoding,
    MedicationKnowledgeProductType,
    MedicationKnowledgeProductTypeCoding,
    MedicationKnowledgeQuantityComparator as MedicationKnowledgeQuantityComparatorModel,
    MedicationKnowledgeRegulatory,
    MedicationKnowledgeRegulatoryAuthorityReferenceType,
    MedicationKnowledgeRegulatorySchedule,
    MedicationKnowledgeRegulatoryScheduleCoding,
    MedicationKnowledgeRegulatorySubstitution,
    MedicationKnowledgeRegulatorySubstitutionTypeCoding,
    MedicationKnowledgeRelated,
    MedicationKnowledgeRelatedReference,
    MedicationKnowledgeRelatedReferenceType,
    MedicationKnowledgeRelatedTypeCoding,
    MedicationKnowledgeStatus as MedicationKnowledgeStatusModel,
)

from ._shared import (
    _ref_kwargs,
    _single_reference_kwargs,
    _validate_ref,
)

if TYPE_CHECKING:
    from app.schemas.medication_knowledge import (
        MedicationKnowledgeCreateSchema,
        MedicationKnowledgePatchSchema,
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


def _coding_kwargs(coding, org_id: str, created_by: str) -> dict:
    return {
        "tenant_id": org_id,
        "created_by": created_by,
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
    }


def _quantity_kwargs(q, prefix: str) -> dict:
    p = f"{prefix}_" if prefix else ""
    if not q:
        return {
            f"{p}value": None,
            f"{p}comparator": None,
            f"{p}unit": None,
            f"{p}system": None,
            f"{p}code": None,
        }
    return {
        f"{p}value": q.value,
        f"{p}comparator": (
            MedicationKnowledgeQuantityComparatorModel[q.comparator.name]
            if q.comparator
            else None
        ),
        f"{p}unit": q.unit,
        f"{p}system": q.system,
        f"{p}code": q.code,
    }


def _ratio_kwargs(r, prefix: str) -> dict:
    num = r.numerator if r else None
    den = r.denominator if r else None
    return {
        **_quantity_kwargs(num, f"{prefix}_numerator"),
        **_quantity_kwargs(den, f"{prefix}_denominator"),
    }


def _money_kwargs(m, prefix: str) -> dict:
    p = f"{prefix}_" if prefix else ""
    if not m:
        return {f"{p}value": None, f"{p}currency": None}
    return {f"{p}value": m.value, f"{p}currency": m.currency}


async def _add_code_codings(session, mk_id: int, org_id: str, codings, actor: str) -> None:
    for c in codings or []:
        session.add(
            MedicationKnowledgeCodeCoding(
                medication_knowledge_pk=mk_id,
                **_coding_kwargs(c, org_id, actor),
            )
        )


async def _add_dose_form_codings(session, mk_id: int, org_id: str, codings, actor: str) -> None:
    for c in codings or []:
        session.add(
            MedicationKnowledgeDoseFormCoding(
                medication_knowledge_pk=mk_id,
                **_coding_kwargs(c, org_id, actor),
            )
        )


async def _add_packaging_type_codings(session, mk_id: int, org_id: str, codings, actor: str) -> None:
    for c in codings or []:
        session.add(
            MedicationKnowledgePackagingTypeCoding(
                medication_knowledge_pk=mk_id,
                **_coding_kwargs(c, org_id, actor),
            )
        )


async def _add_related_knowledge(session, mk_id: int, org_id: str, related_list, actor: str) -> None:
    for item in related_list or []:
        rel = MedicationKnowledgeRelated(
            medication_knowledge_pk=mk_id,
            tenant_id=org_id,
            created_by=actor,
            type_text=item.type.text if item.type else None,
        )
        session.add(rel)
        await session.flush()
        if item.type and item.type.coding:
            for c in item.type.coding:
                session.add(
                    MedicationKnowledgeRelatedTypeCoding(
                        medication_knowledge_related_id=rel.id,
                        **_coding_kwargs(c, org_id, actor),
                    )
                )
        if item.reference:
            for ref_str in item.reference:
                ref_kwargs = _ref_kwargs(
                    "reference", ref_str, None, MedicationKnowledgeRelatedReferenceType
                )
                await _validate_ref(
                    session,
                    org_id,
                    "related_medication_knowledge.reference",
                    ref_kwargs.get("reference_type"),
                    ref_kwargs.get("reference_id"),
                )
                session.add(
                    MedicationKnowledgeRelatedReference(
                        medication_knowledge_related_id=rel.id,
                        tenant_id=org_id,
                        created_by=actor,
                        reference_reference=ref_str,
                        **ref_kwargs,
                    )
                )


async def _add_associated_medications(session, mk_id: int, org_id: str, assoc_list, actor: str) -> None:
    for ref_str in assoc_list or []:
        ref_kwargs = _ref_kwargs(
            "reference", ref_str, None, MedicationKnowledgeAssociatedMedicationReferenceType
        )
        await _validate_ref(
            session,
            org_id,
            "associated_medication",
            ref_kwargs.get("reference_type"),
            ref_kwargs.get("reference_id"),
        )
        session.add(
            MedicationKnowledgeAssociatedMedication(
                medication_knowledge_pk=mk_id,
                tenant_id=org_id,
                created_by=actor,
                reference_reference=ref_str,
                **ref_kwargs,
            )
        )


async def _add_product_types(session, mk_id: int, org_id: str, pt_list, actor: str) -> None:
    for pt in pt_list or []:
        m_pt = MedicationKnowledgeProductType(
            medication_knowledge_pk=mk_id,
            tenant_id=org_id,
            created_by=actor,
            text=pt.text if pt else None,
        )
        session.add(m_pt)
        await session.flush()
        if pt and pt.coding:
            for c in pt.coding:
                session.add(
                    MedicationKnowledgeProductTypeCoding(
                        medication_knowledge_product_type_id=m_pt.id,
                        **_coding_kwargs(c, org_id, actor),
                    )
                )


async def _add_monographs(session, mk_id: int, org_id: str, mono_list, actor: str) -> None:
    for mono in mono_list or []:
        source_kwargs = _single_reference_kwargs(
            "source", mono, MedicationKnowledgeMonographSourceReferenceType
        )
        await _validate_ref(
            session,
            org_id,
            "monograph.source",
            source_kwargs.get("source_type"),
            source_kwargs.get("source_id"),
        )
        m_mono = MedicationKnowledgeMonograph(
            medication_knowledge_pk=mk_id,
            tenant_id=org_id,
            created_by=actor,
            type_text=mono.type.text if mono.type else None,
            **source_kwargs,
        )
        session.add(m_mono)
        await session.flush()
        if mono.type and mono.type.coding:
            for c in mono.type.coding:
                session.add(
                    MedicationKnowledgeMonographTypeCoding(
                        medication_knowledge_monograph_id=m_mono.id,
                        **_coding_kwargs(c, org_id, actor),
                    )
                )


async def _add_ingredients(session, mk_id: int, org_id: str, ing_list, actor: str) -> None:
    for ing in ing_list or []:
        item_kwargs = _single_reference_kwargs(
            "item", ing, MedicationKnowledgeIngredientItemReferenceType
        )
        await _validate_ref(
            session,
            org_id,
            "ingredient.item",
            item_kwargs.get("item_type"),
            item_kwargs.get("item_id"),
        )
        str_kwargs = _ratio_kwargs(ing.strength, "strength")
        m_ing = MedicationKnowledgeIngredient(
            medication_knowledge_pk=mk_id,
            tenant_id=org_id,
            created_by=actor,
            item_codeable_concept_text=(
                ing.item_codeable_concept.text if ing.item_codeable_concept else None
            ),
            **item_kwargs,
            is_active=ing.is_active,
            **str_kwargs,
        )
        session.add(m_ing)
        await session.flush()
        if ing.item_codeable_concept and ing.item_codeable_concept.coding:
            for c in ing.item_codeable_concept.coding:
                session.add(
                    MedicationKnowledgeIngredientItemCoding(
                        medication_knowledge_ingredient_id=m_ing.id,
                        **_coding_kwargs(c, org_id, actor),
                    )
                )


async def _add_intended_routes(session, mk_id: int, org_id: str, ir_list, actor: str) -> None:
    for ir in ir_list or []:
        m_ir = MedicationKnowledgeIntendedRoute(
            medication_knowledge_pk=mk_id,
            tenant_id=org_id,
            created_by=actor,
            text=ir.text if ir else None,
        )
        session.add(m_ir)
        await session.flush()
        if ir and ir.coding:
            for c in ir.coding:
                session.add(
                    MedicationKnowledgeIntendedRouteCoding(
                        medication_knowledge_intended_route_id=m_ir.id,
                        **_coding_kwargs(c, org_id, actor),
                    )
                )


async def _add_costs(session, mk_id: int, org_id: str, cost_list, actor: str) -> None:
    for c in cost_list or []:
        m_cost = MedicationKnowledgeCost(
            medication_knowledge_pk=mk_id,
            tenant_id=org_id,
            created_by=actor,
            type_text=c.type.text if c.type else None,
            source=c.source,
            **_money_kwargs(c.cost, "cost"),
        )
        session.add(m_cost)
        await session.flush()
        if c.type and c.type.coding:
            for coding in c.type.coding:
                session.add(
                    MedicationKnowledgeCostTypeCoding(
                        medication_knowledge_cost_id=m_cost.id,
                        **_coding_kwargs(coding, org_id, actor),
                    )
                )


async def _add_monitoring_programs(session, mk_id: int, org_id: str, mp_list, actor: str) -> None:
    for mp in mp_list or []:
        m_mp = MedicationKnowledgeMonitoringProgram(
            medication_knowledge_pk=mk_id,
            tenant_id=org_id,
            created_by=actor,
            type_text=mp.type.text if mp.type else None,
            name=mp.name,
        )
        session.add(m_mp)
        await session.flush()
        if mp.type and mp.type.coding:
            for coding in mp.type.coding:
                session.add(
                    MedicationKnowledgeMonitoringProgramTypeCoding(
                        medication_knowledge_monitoring_program_id=m_mp.id,
                        **_coding_kwargs(coding, org_id, actor),
                    )
                )


async def _add_administration_guidelines(
    session, mk_id: int, org_id: str, ag_list, actor: str
) -> None:
    for ag in ag_list or []:
        ind_kwargs = _single_reference_kwargs(
            "indication", ag, MedicationKnowledgeAdminGuidelineIndicationReferenceType
        )
        await _validate_ref(
            session,
            org_id,
            "administration_guidelines.indication",
            ind_kwargs.get("indication_type"),
            ind_kwargs.get("indication_id"),
        )
        m_ag = MedicationKnowledgeAdminGuideline(
            medication_knowledge_pk=mk_id,
            tenant_id=org_id,
            created_by=actor,
            indication_codeable_concept_text=(
                ag.indication_codeable_concept.text
                if ag.indication_codeable_concept
                else None
            ),
            **ind_kwargs,
        )
        session.add(m_ag)
        await session.flush()
        if ag.indication_codeable_concept and ag.indication_codeable_concept.coding:
            for coding in ag.indication_codeable_concept.coding:
                session.add(
                    MedicationKnowledgeAdminGuidelineIndicationCoding(
                        medication_knowledge_admin_guideline_id=m_ag.id,
                        **_coding_kwargs(coding, org_id, actor),
                    )
                )
        if ag.dosage:
            for d in ag.dosage:
                m_d = MedicationKnowledgeAdminGuidelineDosage(
                    medication_knowledge_admin_guideline_id=m_ag.id,
                    tenant_id=org_id,
                    created_by=actor,
                    type_text=d.type.text if d.type else None,
                    dosage=d.dosage,
                )
                session.add(m_d)
                await session.flush()
                if d.type and d.type.coding:
                    for coding in d.type.coding:
                        session.add(
                            MedicationKnowledgeAdminGuidelineDosageTypeCoding(
                                medication_knowledge_ag_dosage_id=m_d.id,
                                **_coding_kwargs(coding, org_id, actor),
                            )
                        )
        if ag.patient_characteristics:
            for pc in ag.patient_characteristics:
                qty_kwargs = _quantity_kwargs(
                    pc.characteristic_quantity, "characteristic_quantity"
                )
                m_pc = MedicationKnowledgeAdminGuidelinePatientCharacteristic(
                    medication_knowledge_admin_guideline_id=m_ag.id,
                    tenant_id=org_id,
                    created_by=actor,
                    characteristic_codeable_concept_text=(
                        pc.characteristic_codeable_concept.text
                        if pc.characteristic_codeable_concept
                        else None
                    ),
                    **qty_kwargs,
                    value=pc.value,
                )
                session.add(m_pc)
                await session.flush()
                if (
                    pc.characteristic_codeable_concept
                    and pc.characteristic_codeable_concept.coding
                ):
                    for coding in pc.characteristic_codeable_concept.coding:
                        session.add(
                            MedicationKnowledgeAdminGuidelinePatientCharCoding(
                                medication_knowledge_ag_patient_char_id=m_pc.id,
                                **_coding_kwargs(coding, org_id, actor),
                            )
                        )


async def _add_medicine_classifications(
    session, mk_id: int, org_id: str, mc_list, actor: str
) -> None:
    for mc in mc_list or []:
        m_mc = MedicationKnowledgeMedicineClassification(
            medication_knowledge_pk=mk_id,
            tenant_id=org_id,
            created_by=actor,
            type_text=mc.type.text if mc.type else None,
        )
        session.add(m_mc)
        await session.flush()
        if mc.type and mc.type.coding:
            for coding in mc.type.coding:
                session.add(
                    MedicationKnowledgeMedicineClassificationTypeCoding(
                        medication_knowledge_medicine_classification_id=m_mc.id,
                        **_coding_kwargs(coding, org_id, actor),
                    )
                )
        if mc.classification:
            for item in mc.classification:
                m_item = MedicationKnowledgeMedicineClassificationItem(
                    medication_knowledge_medicine_classification_id=m_mc.id,
                    tenant_id=org_id,
                    created_by=actor,
                    text=item.text if item else None,
                )
                session.add(m_item)
                await session.flush()
                if item and item.coding:
                    for coding in item.coding:
                        session.add(
                            MedicationKnowledgeMedicineClassificationItemCoding(
                                medication_knowledge_med_class_item_id=m_item.id,
                                **_coding_kwargs(coding, org_id, actor),
                            )
                        )


async def _add_drug_characteristics(
    session, mk_id: int, org_id: str, dc_list, actor: str
) -> None:
    for dc in dc_list or []:
        qty_kwargs = _quantity_kwargs(dc.value_quantity, "value_quantity")
        m_dc = MedicationKnowledgeDrugCharacteristic(
            medication_knowledge_pk=mk_id,
            tenant_id=org_id,
            created_by=actor,
            type_text=dc.type.text if dc.type else None,
            value_codeable_concept_text=(
                dc.value_codeable_concept.text if dc.value_codeable_concept else None
            ),
            value_string=dc.value_string,
            **qty_kwargs,
            value_base64_binary=dc.value_base64_binary,
        )
        session.add(m_dc)
        await session.flush()
        if dc.type and dc.type.coding:
            for coding in dc.type.coding:
                session.add(
                    MedicationKnowledgeDrugCharacteristicTypeCoding(
                        medication_knowledge_drug_characteristic_id=m_dc.id,
                        **_coding_kwargs(coding, org_id, actor),
                    )
                )
        if dc.value_codeable_concept and dc.value_codeable_concept.coding:
            for coding in dc.value_codeable_concept.coding:
                session.add(
                    MedicationKnowledgeDrugCharacteristicValueCoding(
                        medication_knowledge_drug_characteristic_id=m_dc.id,
                        **_coding_kwargs(coding, org_id, actor),
                    )
                )


async def _add_contraindications(session, mk_id: int, org_id: str, ci_list, actor: str) -> None:
    for ref_str in ci_list or []:
        ref_kwargs = _ref_kwargs(
            "reference", ref_str, None, MedicationKnowledgeContraindicationReferenceType
        )
        await _validate_ref(
            session,
            org_id,
            "contraindication",
            ref_kwargs.get("reference_type"),
            ref_kwargs.get("reference_id"),
        )
        session.add(
            MedicationKnowledgeContraindication(
                medication_knowledge_pk=mk_id,
                tenant_id=org_id,
                created_by=actor,
                reference_reference=ref_str,
                **ref_kwargs,
            )
        )


async def _add_regulatory(session, mk_id: int, org_id: str, reg_list, actor: str) -> None:
    for reg in reg_list or []:
        auth_kwargs = _single_reference_kwargs(
            "regulatory_authority", reg, MedicationKnowledgeRegulatoryAuthorityReferenceType
        )
        await _validate_ref(
            session,
            org_id,
            "regulatory.regulatory_authority",
            auth_kwargs.get("regulatory_authority_type"),
            auth_kwargs.get("regulatory_authority_id"),
        )
        md = reg.max_dispense
        qty_kwargs = (
            _quantity_kwargs(md.quantity, "max_dispense_quantity")
            if md
            else _quantity_kwargs(None, "max_dispense_quantity")
        )
        period_kwargs = (
            _quantity_kwargs(md.period, "max_dispense_period")
            if md
            else _quantity_kwargs(None, "max_dispense_period")
        )
        m_reg = MedicationKnowledgeRegulatory(
            medication_knowledge_pk=mk_id,
            tenant_id=org_id,
            created_by=actor,
            **auth_kwargs,
            **qty_kwargs,
            **period_kwargs,
        )
        session.add(m_reg)
        await session.flush()
        if reg.substitution:
            for s in reg.substitution:
                m_sub = MedicationKnowledgeRegulatorySubstitution(
                    medication_knowledge_regulatory_id=m_reg.id,
                    tenant_id=org_id,
                    created_by=actor,
                    type_text=s.type.text if s.type else None,
                    allowed=s.allowed,
                )
                session.add(m_sub)
                await session.flush()
                if s.type and s.type.coding:
                    for coding in s.type.coding:
                        session.add(
                            MedicationKnowledgeRegulatorySubstitutionTypeCoding(
                                medication_knowledge_reg_sub_id=m_sub.id,
                                **_coding_kwargs(coding, org_id, actor),
                            )
                        )
        if reg.schedule:
            for sc in reg.schedule:
                m_sc = MedicationKnowledgeRegulatorySchedule(
                    medication_knowledge_regulatory_id=m_reg.id,
                    tenant_id=org_id,
                    created_by=actor,
                    schedule_text=sc.schedule.text if sc.schedule else None,
                )
                session.add(m_sc)
                await session.flush()
                if sc.schedule and sc.schedule.coding:
                    for coding in sc.schedule.coding:
                        session.add(
                            MedicationKnowledgeRegulatoryScheduleCoding(
                                medication_knowledge_reg_sched_id=m_sc.id,
                                **_coding_kwargs(coding, org_id, actor),
                            )
                        )


async def _add_kinetics(session, mk_id: int, org_id: str, kin_list, actor: str) -> None:
    for k in kin_list or []:
        hlp_kwargs = _quantity_kwargs(k.half_life_period, "half_life_period")
        m_k = MedicationKnowledgeKinetics(
            medication_knowledge_pk=mk_id,
            tenant_id=org_id,
            created_by=actor,
            **hlp_kwargs,
        )
        session.add(m_k)
        await session.flush()
        if k.area_under_curve:
            for auc in k.area_under_curve:
                session.add(
                    MedicationKnowledgeKineticsAreaUnderCurve(
                        medication_knowledge_kinetics_id=m_k.id,
                        tenant_id=org_id,
                        created_by=actor,
                        **_quantity_kwargs(auc, ""),
                    )
                )
        if k.lethal_dose_50:
            for ld in k.lethal_dose_50:
                session.add(
                    MedicationKnowledgeKineticsLethalDose50(
                        medication_knowledge_kinetics_id=m_k.id,
                        tenant_id=org_id,
                        created_by=actor,
                        **_quantity_kwargs(ld, ""),
                    )
                )


class _FullMixin:
    """Full-payload create and patch operations for MedicationKnowledge."""

    async def create_full(
        self,
        payload: MedicationKnowledgeCreateSchema,
        org_id: str,
        created_by: str,
    ) -> MedicationKnowledgeModel:
        async with self.session_factory() as session:
            # 1. Resolve & validate manufacturer reference
            mfg_kwargs = _single_reference_kwargs(
                "manufacturer", payload, MedicationKnowledgeManufacturerReferenceType
            )
            await _validate_ref(
                session,
                org_id,
                "manufacturer",
                mfg_kwargs.get("manufacturer_type"),
                mfg_kwargs.get("manufacturer_id"),
            )

            # Packaging kwargs
            pkg = payload.packaging
            pkg_type_text = pkg.type.text if pkg and pkg.type else None
            pkg_qty_kwargs = (
                _quantity_kwargs(pkg.quantity, "packaging_quantity")
                if pkg
                else _quantity_kwargs(None, "packaging_quantity")
            )

            amount_kwargs = _quantity_kwargs(payload.amount, "amount")

            # 2. Main row
            mk = MedicationKnowledgeModel(
                tenant_id=org_id,
                created_by=created_by,
                code_text=payload.code.text if payload.code else None,
                status=(
                    MedicationKnowledgeStatusModel[payload.status.name]
                    if payload.status
                    else None
                ),
                **mfg_kwargs,
                dose_form_text=payload.dose_form.text if payload.dose_form else None,
                **amount_kwargs,
                synonym=list(payload.synonym) if payload.synonym else None,
                preparation_instruction=payload.preparation_instruction,
                packaging_type_text=pkg_type_text,
                **pkg_qty_kwargs,
                extension=payload.extension if payload.extension is not None else [],
            )
            session.add(mk)
            await session.flush()

            # 3. Add sub-resources
            if payload.code and payload.code.coding:
                await _add_code_codings(session, mk.id, org_id, payload.code.coding, created_by)
            if payload.dose_form and payload.dose_form.coding:
                await _add_dose_form_codings(session, mk.id, org_id, payload.dose_form.coding, created_by)
            if pkg and pkg.type and pkg.type.coding:
                await _add_packaging_type_codings(session, mk.id, org_id, pkg.type.coding, created_by)
            await _add_related_knowledge(session, mk.id, org_id, payload.related_medication_knowledge, created_by)
            await _add_associated_medications(session, mk.id, org_id, payload.associated_medication, created_by)
            await _add_product_types(session, mk.id, org_id, payload.product_type, created_by)
            await _add_monographs(session, mk.id, org_id, payload.monograph, created_by)
            await _add_ingredients(session, mk.id, org_id, payload.ingredient, created_by)
            await _add_intended_routes(session, mk.id, org_id, payload.intended_route, created_by)
            await _add_costs(session, mk.id, org_id, payload.cost, created_by)
            await _add_monitoring_programs(session, mk.id, org_id, payload.monitoring_program, created_by)
            await _add_administration_guidelines(session, mk.id, org_id, payload.administration_guidelines, created_by)
            await _add_medicine_classifications(session, mk.id, org_id, payload.medicine_classification, created_by)
            await _add_drug_characteristics(session, mk.id, org_id, payload.drug_characteristic, created_by)
            await _add_contraindications(session, mk.id, org_id, payload.contraindication, created_by)
            await _add_regulatory(session, mk.id, org_id, payload.regulatory, created_by)
            await _add_kinetics(session, mk.id, org_id, payload.kinetics, created_by)

            pub_id = mk.medication_knowledge_id
            await session.commit()

        return await self.get_by_medication_knowledge_id_in_org(pub_id, org_id)

    async def patch_full(
        self,
        medication_knowledge_id: int,
        payload: MedicationKnowledgePatchSchema,
        org_id: str,
        updated_by: str,
    ) -> MedicationKnowledgeModel | None:
        async with self.session_factory() as session:
            stmt = select(MedicationKnowledgeModel).where(
                MedicationKnowledgeModel.medication_knowledge_id == medication_knowledge_id,
                MedicationKnowledgeModel.tenant_id == org_id,
            )
            res = await session.execute(stmt)
            mk = res.scalar_one_or_none()
            if not mk:
                return None

            provided = payload.model_fields_set

            if "status" in provided:
                mk.status = (
                    MedicationKnowledgeStatusModel[payload.status.name]
                    if payload.status
                    else None
                )

            if "code" in provided:
                mk.code_text = payload.code.text if payload.code else None
                await session.execute(
                    delete(MedicationKnowledgeCodeCoding).where(
                        MedicationKnowledgeCodeCoding.medication_knowledge_pk == mk.id
                    )
                )
                if payload.code and payload.code.coding:
                    await _add_code_codings(
                        session, mk.id, org_id, payload.code.coding, updated_by
                    )

            if "dose_form" in provided:
                mk.dose_form_text = payload.dose_form.text if payload.dose_form else None
                await session.execute(
                    delete(MedicationKnowledgeDoseFormCoding).where(
                        MedicationKnowledgeDoseFormCoding.medication_knowledge_pk == mk.id
                    )
                )
                if payload.dose_form and payload.dose_form.coding:
                    await _add_dose_form_codings(
                        session, mk.id, org_id, payload.dose_form.coding, updated_by
                    )

            if provided & _MANUFACTURER_FIELDS:
                mfg_kwargs = _single_reference_kwargs(
                    "manufacturer", payload, MedicationKnowledgeManufacturerReferenceType
                )
                await _validate_ref(
                    session,
                    org_id,
                    "manufacturer",
                    mfg_kwargs.get("manufacturer_type"),
                    mfg_kwargs.get("manufacturer_id"),
                )
                for k, v in mfg_kwargs.items():
                    setattr(mk, k, v)

            if "amount" in provided:
                amount_kwargs = _quantity_kwargs(payload.amount, "amount")
                for k, v in amount_kwargs.items():
                    setattr(mk, k, v)

            if "synonym" in provided:
                mk.synonym = list(payload.synonym) if payload.synonym is not None else None

            if "preparation_instruction" in provided:
                mk.preparation_instruction = payload.preparation_instruction

            if "packaging" in provided:
                pkg = payload.packaging
                mk.packaging_type_text = pkg.type.text if pkg and pkg.type else None
                pkg_qty_kwargs = (
                    _quantity_kwargs(pkg.quantity, "packaging_quantity")
                    if pkg
                    else _quantity_kwargs(None, "packaging_quantity")
                )
                for k, v in pkg_qty_kwargs.items():
                    setattr(mk, k, v)
                await session.execute(
                    delete(MedicationKnowledgePackagingTypeCoding).where(
                        MedicationKnowledgePackagingTypeCoding.medication_knowledge_pk == mk.id
                    )
                )
                if pkg and pkg.type and pkg.type.coding:
                    await _add_packaging_type_codings(
                        session, mk.id, org_id, pkg.type.coding, updated_by
                    )

            if "extension" in provided:
                mk.extension = list(payload.extension) if payload.extension else []

            if "related_medication_knowledge" in provided:
                await session.execute(
                    delete(MedicationKnowledgeRelated).where(
                        MedicationKnowledgeRelated.medication_knowledge_pk == mk.id
                    )
                )
                await _add_related_knowledge(
                    session, mk.id, org_id, payload.related_medication_knowledge, updated_by
                )

            if "associated_medication" in provided:
                await session.execute(
                    delete(MedicationKnowledgeAssociatedMedication).where(
                        MedicationKnowledgeAssociatedMedication.medication_knowledge_pk == mk.id
                    )
                )
                await _add_associated_medications(
                    session, mk.id, org_id, payload.associated_medication, updated_by
                )

            if "product_type" in provided:
                await session.execute(
                    delete(MedicationKnowledgeProductType).where(
                        MedicationKnowledgeProductType.medication_knowledge_pk == mk.id
                    )
                )
                await _add_product_types(
                    session, mk.id, org_id, payload.product_type, updated_by
                )

            if "monograph" in provided:
                await session.execute(
                    delete(MedicationKnowledgeMonograph).where(
                        MedicationKnowledgeMonograph.medication_knowledge_pk == mk.id
                    )
                )
                await _add_monographs(
                    session, mk.id, org_id, payload.monograph, updated_by
                )

            if "ingredient" in provided:
                await session.execute(
                    delete(MedicationKnowledgeIngredient).where(
                        MedicationKnowledgeIngredient.medication_knowledge_pk == mk.id
                    )
                )
                await _add_ingredients(
                    session, mk.id, org_id, payload.ingredient, updated_by
                )

            if "intended_route" in provided:
                await session.execute(
                    delete(MedicationKnowledgeIntendedRoute).where(
                        MedicationKnowledgeIntendedRoute.medication_knowledge_pk == mk.id
                    )
                )
                await _add_intended_routes(
                    session, mk.id, org_id, payload.intended_route, updated_by
                )

            if "cost" in provided:
                await session.execute(
                    delete(MedicationKnowledgeCost).where(
                        MedicationKnowledgeCost.medication_knowledge_pk == mk.id
                    )
                )
                await _add_costs(session, mk.id, org_id, payload.cost, updated_by)

            if "monitoring_program" in provided:
                await session.execute(
                    delete(MedicationKnowledgeMonitoringProgram).where(
                        MedicationKnowledgeMonitoringProgram.medication_knowledge_pk == mk.id
                    )
                )
                await _add_monitoring_programs(
                    session, mk.id, org_id, payload.monitoring_program, updated_by
                )

            if "administration_guidelines" in provided:
                await session.execute(
                    delete(MedicationKnowledgeAdminGuideline).where(
                        MedicationKnowledgeAdminGuideline.medication_knowledge_pk == mk.id
                    )
                )
                await _add_administration_guidelines(
                    session, mk.id, org_id, payload.administration_guidelines, updated_by
                )

            if "medicine_classification" in provided:
                await session.execute(
                    delete(MedicationKnowledgeMedicineClassification).where(
                        MedicationKnowledgeMedicineClassification.medication_knowledge_pk == mk.id
                    )
                )
                await _add_medicine_classifications(
                    session, mk.id, org_id, payload.medicine_classification, updated_by
                )

            if "drug_characteristic" in provided:
                await session.execute(
                    delete(MedicationKnowledgeDrugCharacteristic).where(
                        MedicationKnowledgeDrugCharacteristic.medication_knowledge_pk == mk.id
                    )
                )
                await _add_drug_characteristics(
                    session, mk.id, org_id, payload.drug_characteristic, updated_by
                )

            if "contraindication" in provided:
                await session.execute(
                    delete(MedicationKnowledgeContraindication).where(
                        MedicationKnowledgeContraindication.medication_knowledge_pk == mk.id
                    )
                )
                await _add_contraindications(
                    session, mk.id, org_id, payload.contraindication, updated_by
                )

            if "regulatory" in provided:
                await session.execute(
                    delete(MedicationKnowledgeRegulatory).where(
                        MedicationKnowledgeRegulatory.medication_knowledge_pk == mk.id
                    )
                )
                await _add_regulatory(
                    session, mk.id, org_id, payload.regulatory, updated_by
                )

            if "kinetics" in provided:
                await session.execute(
                    delete(MedicationKnowledgeKinetics).where(
                        MedicationKnowledgeKinetics.medication_knowledge_pk == mk.id
                    )
                )
                await _add_kinetics(
                    session, mk.id, org_id, payload.kinetics, updated_by
                )

            mk.updated_by = updated_by
            pub_id = mk.medication_knowledge_id
            await session.commit()

        return await self.get_by_medication_knowledge_id_in_org(pub_id, org_id)
