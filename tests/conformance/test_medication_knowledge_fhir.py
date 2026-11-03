"""FHIR R4 conformance for `to_fhir_medication_knowledge()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt
from decimal import Decimal

import pytest

from app.fhir.mappers.medication_knowledge import to_fhir_medication_knowledge
from app.models.enums import IdentifierUse
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
    MedicationKnowledgeQuantityComparator,
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
    MedicationKnowledgeStatus,
)

from .support import assert_valid

medication_knowledge_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.medication_knowledge_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "code_codings",
    "dose_form_codings",
    "packaging_type_codings",
    "related_knowledge",
    "associated_medications",
    "product_types",
    "monographs",
    "ingredients",
    "intended_routes",
    "costs",
    "monitoring_programs",
    "administration_guidelines",
    "medicine_classifications",
    "drug_characteristics",
    "contraindications",
    "regulatory",
    "kinetics",
)


def _medication_knowledge(**overrides) -> MedicationKnowledgeModel:
    fields = {
        "id": 1,
        "medication_knowledge_id": 600001,
        "tenant_id": "org-test",
        "status": MedicationKnowledgeStatus.active,
        "code_text": "Amoxicillin 500mg capsule",
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = MedicationKnowledgeModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_medication_knowledge_minimal_conformance():
    m = _medication_knowledge()
    m.code_codings = [
        MedicationKnowledgeCodeCoding(
            medication_knowledge_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="372687004",
            display="Amoxicillin 500mg capsule",
            created_by="u-test",
        )
    ]
    fhir = to_fhir_medication_knowledge(m)
    assert_valid(medication_knowledge_pb2.MedicationKnowledge, fhir)


def test_medication_knowledge_full_conformance():
    m = _medication_knowledge(
        manufacturer_reference="Organization/190001",
        manufacturer_type=MedicationKnowledgeManufacturerReferenceType.Organization,
        manufacturer_id=190001,
        manufacturer_display="Pharma Corp",
        dose_form_text="Capsule",
        amount_value=Decimal("500"),
        amount_unit="mg",
        amount_system="http://unitsofmeasure.org",
        amount_code="mg",
        synonym=["Amoxil", "Trimox"],
        preparation_instruction="Take with water before meals.",
        packaging_type_text="Bottle",
        packaging_quantity_value=Decimal("100"),
        packaging_quantity_unit="capsule",
    )

    m.code_codings = [
        MedicationKnowledgeCodeCoding(
            medication_knowledge_pk=1,
            tenant_id="org-test",
            system="http://www.nlm.nih.gov/research/umls/rxnorm",
            code="308182",
            display="Amoxicillin 500 MG Oral Capsule",
            created_by="u-test",
        )
    ]

    m.dose_form_codings = [
        MedicationKnowledgeDoseFormCoding(
            medication_knowledge_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="385055001",
            display="Oral Capsule",
            created_by="u-test",
        )
    ]

    m.packaging_type_codings = [
        MedicationKnowledgePackagingTypeCoding(
            medication_knowledge_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/medicationknowledge-package-type",
            code="bot",
            display="Bottle",
            created_by="u-test",
        )
    ]

    rel = MedicationKnowledgeRelated(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        type_text="replaces",
        created_by="u-test",
    )
    rel.type_codings = [
        MedicationKnowledgeRelatedTypeCoding(
            medication_knowledge_related_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/medicationknowledge-related-type",
            code="replaces",
            display="Replaces",
            created_by="u-test",
        )
    ]
    rel.references = [
        MedicationKnowledgeRelatedReference(
            medication_knowledge_related_id=1,
            tenant_id="org-test",
            reference_reference="MedicationKnowledge/600000",
            reference_type=MedicationKnowledgeRelatedReferenceType.MedicationKnowledge,
            reference_id=600000,
            reference_display="Old Amoxicillin",
            created_by="u-test",
        )
    ]
    m.related_knowledge = [rel]

    assoc = MedicationKnowledgeAssociatedMedication(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        reference_reference="Medication/250001",
        reference_type=MedicationKnowledgeAssociatedMedicationReferenceType.Medication,
        reference_id=250001,
        reference_display="Amoxicillin 500mg",
        created_by="u-test",
    )
    m.associated_medications = [assoc]

    pt = MedicationKnowledgeProductType(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        text="Prescription Only",
        created_by="u-test",
    )
    pt.codings = [
        MedicationKnowledgeProductTypeCoding(
            medication_knowledge_product_type_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/medication-knowledge-product-type",
            code="rx",
            display="Prescription",
            created_by="u-test",
        )
    ]
    m.product_types = [pt]

    mono = MedicationKnowledgeMonograph(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        type_text="Prescribing Information",
        source_reference="DocumentReference/320001",
        source_type=MedicationKnowledgeMonographSourceReferenceType.DocumentReference,
        source_id=320001,
        source_display="FDA Prescribing Info",
        created_by="u-test",
    )
    mono.type_codings = [
        MedicationKnowledgeMonographTypeCoding(
            medication_knowledge_monograph_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/medication-knowledge-monograph-type",
            code="pi",
            display="Prescribing Information",
            created_by="u-test",
        )
    ]
    m.monographs = [mono]

    ing = MedicationKnowledgeIngredient(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        item_reference="Substance/1",
        item_type=MedicationKnowledgeIngredientItemReferenceType.Substance,
        item_id=1,
        item_display="Amoxicillin Trihydrate",
        is_active=True,
        strength_numerator_value=Decimal("500"),
        strength_numerator_unit="mg",
        strength_numerator_system="http://unitsofmeasure.org",
        strength_numerator_code="mg",
        strength_denominator_value=Decimal("1"),
        strength_denominator_unit="capsule",
        strength_denominator_system="http://unitsofmeasure.org",
        strength_denominator_code="1",
        created_by="u-test",
    )
    ing.item_codings = [
        MedicationKnowledgeIngredientItemCoding(
            medication_knowledge_ingredient_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="27658006",
            display="Amoxicillin",
            created_by="u-test",
        )
    ]
    m.ingredients = [ing]

    ir = MedicationKnowledgeIntendedRoute(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        text="Oral",
        created_by="u-test",
    )
    ir.codings = [
        MedicationKnowledgeIntendedRouteCoding(
            medication_knowledge_intended_route_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="260548002",
            display="Oral",
            created_by="u-test",
        )
    ]
    m.intended_routes = [ir]

    cost = MedicationKnowledgeCost(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        type_text="Wholesale",
        source="Acme Supplies",
        cost_value=Decimal("15.50"),
        cost_currency="USD",
        created_by="u-test",
    )
    cost.type_codings = [
        MedicationKnowledgeCostTypeCoding(
            medication_knowledge_cost_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/medication-knowledge-cost-type",
            code="wholesale",
            display="Wholesale Price",
            created_by="u-test",
        )
    ]
    m.costs = [cost]

    mp = MedicationKnowledgeMonitoringProgram(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        type_text="REMS",
        name="Safe Use Program",
        created_by="u-test",
    )
    mp.type_codings = [
        MedicationKnowledgeMonitoringProgramTypeCoding(
            medication_knowledge_monitoring_program_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/medication-knowledge-monitoring-program-type",
            code="rems",
            display="Risk Evaluation and Mitigation Strategy",
            created_by="u-test",
        )
    ]
    m.monitoring_programs = [mp]

    ag = MedicationKnowledgeAdminGuideline(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        indication_codeable_concept_text="Bacterial Infection",
        created_by="u-test",
    )
    ag.indication_codings = [
        MedicationKnowledgeAdminGuidelineIndicationCoding(
            medication_knowledge_admin_guideline_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="87628006",
            display="Bacterial infectious disease",
            created_by="u-test",
        )
    ]
    ag_dosage = MedicationKnowledgeAdminGuidelineDosage(
        medication_knowledge_admin_guideline_id=1,
        tenant_id="org-test",
        type_text="Standard Adult Dose",
        dosage=[{"text": "500 mg every 8 hours"}],
        created_by="u-test",
    )
    ag_dosage.type_codings = [
        MedicationKnowledgeAdminGuidelineDosageTypeCoding(
            medication_knowledge_ag_dosage_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/dosage-type",
            code="adult",
            display="Adult",
            created_by="u-test",
        )
    ]
    ag.dosages = [ag_dosage]

    pc = MedicationKnowledgeAdminGuidelinePatientCharacteristic(
        medication_knowledge_admin_guideline_id=1,
        tenant_id="org-test",
        characteristic_codeable_concept_text="Age Group",
        value=["Adult"],
        created_by="u-test",
    )
    pc.characteristic_codings = [
        MedicationKnowledgeAdminGuidelinePatientCharCoding(
            medication_knowledge_ag_patient_char_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="424144002",
            display="Age group",
            created_by="u-test",
        )
    ]
    ag.patient_characteristics = [pc]
    m.administration_guidelines = [ag]

    mc = MedicationKnowledgeMedicineClassification(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        type_text="ATC",
        created_by="u-test",
    )
    mc.type_codings = [
        MedicationKnowledgeMedicineClassificationTypeCoding(
            medication_knowledge_medicine_classification_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/medicine-classification-type",
            code="atc",
            display="Anatomical Therapeutic Chemical",
            created_by="u-test",
        )
    ]
    mc_item = MedicationKnowledgeMedicineClassificationItem(
        medication_knowledge_medicine_classification_id=1,
        tenant_id="org-test",
        text="Beta-lactamase sensitive penicillins",
        created_by="u-test",
    )
    mc_item.codings = [
        MedicationKnowledgeMedicineClassificationItemCoding(
            medication_knowledge_med_class_item_id=1,
            tenant_id="org-test",
            system="http://www.whocc.no/atc",
            code="J01CA04",
            display="amoxicillin",
            created_by="u-test",
        )
    ]
    mc.classification_items = [mc_item]
    m.medicine_classifications = [mc]

    dc = MedicationKnowledgeDrugCharacteristic(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        type_text="Color",
        value_string="Yellow / Maroon",
        created_by="u-test",
    )
    dc.type_codings = [
        MedicationKnowledgeDrugCharacteristicTypeCoding(
            medication_knowledge_drug_characteristic_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/medicationknowledge-characteristic",
            code="color",
            display="Color",
            created_by="u-test",
        )
    ]
    m.drug_characteristics = [dc]

    ci = MedicationKnowledgeContraindication(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        reference_reference="DetectedIssue/540001",
        reference_type=MedicationKnowledgeContraindicationReferenceType.DetectedIssue,
        reference_id=540001,
        reference_display="Penicillin allergy issue",
        created_by="u-test",
    )
    m.contraindications = [ci]

    reg = MedicationKnowledgeRegulatory(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        regulatory_authority_reference="Organization/190001",
        regulatory_authority_type=MedicationKnowledgeRegulatoryAuthorityReferenceType.Organization,
        regulatory_authority_id=190001,
        regulatory_authority_display="FDA",
        max_dispense_quantity_value=Decimal("30"),
        max_dispense_quantity_unit="capsule",
        max_dispense_period_value=Decimal("30"),
        max_dispense_period_unit="days",
        max_dispense_period_system="http://unitsofmeasure.org",
        max_dispense_period_code="d",
        created_by="u-test",
    )
    sub = MedicationKnowledgeRegulatorySubstitution(
        medication_knowledge_regulatory_id=1,
        tenant_id="org-test",
        type_text="Generic",
        allowed=True,
        created_by="u-test",
    )
    sub.type_codings = [
        MedicationKnowledgeRegulatorySubstitutionTypeCoding(
            medication_knowledge_reg_sub_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/medicationknowledge-substitution",
            code="generic",
            display="Generic Substitution",
            created_by="u-test",
        )
    ]
    reg.substitutions = [sub]
    sched = MedicationKnowledgeRegulatorySchedule(
        medication_knowledge_regulatory_id=1,
        tenant_id="org-test",
        schedule_text="Schedule IV",
        created_by="u-test",
    )
    sched.schedule_codings = [
        MedicationKnowledgeRegulatoryScheduleCoding(
            medication_knowledge_reg_sched_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/medication-schedule",
            code="schedule4",
            display="Schedule IV",
            created_by="u-test",
        )
    ]
    reg.schedules = [sched]
    m.regulatory = [reg]

    kin = MedicationKnowledgeKinetics(
        medication_knowledge_pk=1,
        tenant_id="org-test",
        half_life_period_value=Decimal("1.5"),
        half_life_period_unit="h",
        half_life_period_system="http://unitsofmeasure.org",
        half_life_period_code="h",
        created_by="u-test",
    )
    auc = MedicationKnowledgeKineticsAreaUnderCurve(
        medication_knowledge_kinetics_id=1,
        tenant_id="org-test",
        value=Decimal("25.5"),
        unit="mg*h/L",
        system="http://unitsofmeasure.org",
        code="mg*h/L",
        created_by="u-test",
    )
    kin.area_under_curve = [auc]
    ld50 = MedicationKnowledgeKineticsLethalDose50(
        medication_knowledge_kinetics_id=1,
        tenant_id="org-test",
        value=Decimal("5000"),
        unit="mg/kg",
        system="http://unitsofmeasure.org",
        code="mg/kg",
        created_by="u-test",
    )
    kin.lethal_dose_50 = [ld50]
    m.kinetics = [kin]

    fhir = to_fhir_medication_knowledge(m)
    assert_valid(medication_knowledge_pb2.MedicationKnowledge, fhir)
