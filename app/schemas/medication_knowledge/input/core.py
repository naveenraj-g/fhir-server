from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse, MedicationKnowledgeStatus
from app.schemas.medication_knowledge.input.admin_guideline import (
    MedicationKnowledgeAdminGuidelineInput,
)
from app.schemas.medication_knowledge.input.codeable_concept import (
    MedicationKnowledgeCodeableConceptInput,
)
from app.schemas.medication_knowledge.input.cost import (
    MedicationKnowledgeCostInput,
)
from app.schemas.medication_knowledge.input.drug_characteristic import (
    MedicationKnowledgeDrugCharacteristicInput,
)
from app.schemas.medication_knowledge.input.ingredient import (
    MedicationKnowledgeIngredientInput,
)
from app.schemas.medication_knowledge.input.kinetics import (
    MedicationKnowledgeKineticsInput,
)
from app.schemas.medication_knowledge.input.medicine_classification import (
    MedicationKnowledgeMedicineClassificationInput,
)
from app.schemas.medication_knowledge.input.monitoring_program import (
    MedicationKnowledgeMonitoringProgramInput,
)
from app.schemas.medication_knowledge.input.monograph import (
    MedicationKnowledgeMonographInput,
)
from app.schemas.medication_knowledge.input.packaging import (
    MedicationKnowledgePackagingInput,
)
from app.schemas.medication_knowledge.input.quantity import (
    MedicationKnowledgeQuantityInput,
)
from app.schemas.medication_knowledge.input.regulatory import (
    MedicationKnowledgeRegulatoryInput,
)
from app.schemas.medication_knowledge.input.related import (
    MedicationKnowledgeRelatedInput,
)

_CREATE_EXAMPLE: dict[str, Any] = {
    "status": "active",
    "code": {
        "text": "Amoxicillin 500mg capsule",
        "coding": [
            {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "308182",
                "display": "Amoxicillin 500 MG Oral Capsule",
            }
        ],
    },
    "dose_form": {
        "text": "Oral Capsule",
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "385055001",
                "display": "Oral Capsule",
            }
        ],
    },
    "synonym": ["Amoxil"],
}


class MedicationKnowledgeCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _CREATE_EXAMPLE},
    )

    code: MedicationKnowledgeCodeableConceptInput | None = Field(
        None, description="Code that identifies this medication."
    )
    status: MedicationKnowledgeStatus | None = Field(
        None, description="active | inactive | entered-in-error."
    )
    manufacturer: str | None = Field(
        None,
        description="Manufacturer of the item. Reference(Organization), e.g. 'Organization/190001'.",
    )
    manufacturer_display: str | None = Field(
        None, description="Display text for manufacturer reference."
    )
    manufacturer_identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier — purpose."
    )
    manufacturer_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — type system."
    )
    manufacturer_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — type version."
    )
    manufacturer_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — type code."
    )
    manufacturer_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — type display."
    )
    manufacturer_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — type user selected."
    )
    manufacturer_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — type text."
    )
    manufacturer_identifier_system: str | None = Field(
        None, description="Fallback identifier — system."
    )
    manufacturer_identifier_value: str | None = Field(
        None, description="Fallback identifier — value."
    )
    manufacturer_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — period start."
    )
    manufacturer_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — period end."
    )

    dose_form: MedicationKnowledgeCodeableConceptInput | None = Field(
        None, description="powder | tablets | capsule +"
    )
    amount: MedicationKnowledgeQuantityInput | None = Field(
        None, description="Amount of product in package."
    )
    synonym: list[str] | None = Field(
        None, description="Additional names for a medication."
    )
    related_medication_knowledge: list[MedicationKnowledgeRelatedInput] | None = Field(
        None, description="Associated or related medication information."
    )
    associated_medication: list[str] | None = Field(
        None, description="The set of associated medications. Reference(Medication)."
    )
    product_type: list[MedicationKnowledgeCodeableConceptInput] | None = Field(
        None, description="Category of the medication or product (e.g. OTC, Rx)."
    )
    monograph: list[MedicationKnowledgeMonographInput] | None = Field(
        None, description="Associated documentation about the medication."
    )
    ingredient: list[MedicationKnowledgeIngredientInput] | None = Field(
        None, description="Active or inactive ingredients."
    )
    preparation_instruction: str | None = Field(
        None, description="The instructions for preparing the medication."
    )
    intended_route: list[MedicationKnowledgeCodeableConceptInput] | None = Field(
        None, description="The intended route of administration."
    )
    cost: list[MedicationKnowledgeCostInput] | None = Field(
        None, description="The pricing of the medication."
    )
    monitoring_program: list[MedicationKnowledgeMonitoringProgramInput] | None = Field(
        None, description="Program under which the medication is monitored."
    )
    administration_guidelines: list[MedicationKnowledgeAdminGuidelineInput] | None = Field(
        None, description="Guidelines for medication administration."
    )
    medicine_classification: list[MedicationKnowledgeMedicineClassificationInput] | None = Field(
        None, description="Categorization of the medication within a classification system."
    )
    packaging: MedicationKnowledgePackagingInput | None = Field(
        None, description="Details about packaged medications."
    )
    drug_characteristic: list[MedicationKnowledgeDrugCharacteristicInput] | None = Field(
        None, description="Specifies descriptive properties of the medicine."
    )
    contraindication: list[str] | None = Field(
        None, description="Potential clinical issue with or between medication(s). Reference(DetectedIssue)."
    )
    regulatory: list[MedicationKnowledgeRegulatoryInput] | None = Field(
        None, description="Regulatory information about a medication."
    )
    kinetics: list[MedicationKnowledgeKineticsInput] | None = Field(
        None, description="The time course of drug absorption, distribution, metabolism and excretion of a medication from the body."
    )
    extension: list[dict] | None = Field(
        None, description="Additional content defined by implementations."
    )


class MedicationKnowledgePatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: MedicationKnowledgeCodeableConceptInput | None = Field(None, description="Code that identifies this medication.")
    status: MedicationKnowledgeStatus | None = Field(None, description="active | inactive | entered-in-error.")
    manufacturer: str | None = Field(None, description="Manufacturer of the item. Reference(Organization).")
    manufacturer_display: str | None = Field(None, description="Display text for manufacturer reference.")
    manufacturer_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    manufacturer_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    manufacturer_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    manufacturer_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    manufacturer_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    manufacturer_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    manufacturer_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    manufacturer_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    manufacturer_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    manufacturer_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    manufacturer_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    dose_form: MedicationKnowledgeCodeableConceptInput | None = Field(None, description="powder | tablets | capsule +")
    amount: MedicationKnowledgeQuantityInput | None = Field(None, description="Amount of product in package.")
    synonym: list[str] | None = Field(None, description="Additional names for a medication.")
    related_medication_knowledge: list[MedicationKnowledgeRelatedInput] | None = Field(None, description="Associated or related medication information.")
    associated_medication: list[str] | None = Field(None, description="The set of associated medications. Reference(Medication).")
    product_type: list[MedicationKnowledgeCodeableConceptInput] | None = Field(None, description="Category of the medication or product.")
    monograph: list[MedicationKnowledgeMonographInput] | None = Field(None, description="Associated documentation about the medication.")
    ingredient: list[MedicationKnowledgeIngredientInput] | None = Field(None, description="Active or inactive ingredients.")
    preparation_instruction: str | None = Field(None, description="The instructions for preparing the medication.")
    intended_route: list[MedicationKnowledgeCodeableConceptInput] | None = Field(None, description="The intended route of administration.")
    cost: list[MedicationKnowledgeCostInput] | None = Field(None, description="The pricing of the medication.")
    monitoring_program: list[MedicationKnowledgeMonitoringProgramInput] | None = Field(None, description="Program under which the medication is monitored.")
    administration_guidelines: list[MedicationKnowledgeAdminGuidelineInput] | None = Field(None, description="Guidelines for medication administration.")
    medicine_classification: list[MedicationKnowledgeMedicineClassificationInput] | None = Field(None, description="Categorization of the medication within a classification system.")
    packaging: MedicationKnowledgePackagingInput | None = Field(None, description="Details about packaged medications.")
    drug_characteristic: list[MedicationKnowledgeDrugCharacteristicInput] | None = Field(None, description="Specifies descriptive properties of the medicine.")
    contraindication: list[str] | None = Field(None, description="Potential clinical issue with or between medication(s). Reference(DetectedIssue).")
    regulatory: list[MedicationKnowledgeRegulatoryInput] | None = Field(None, description="Regulatory information about a medication.")
    kinetics: list[MedicationKnowledgeKineticsInput] | None = Field(None, description="The time course of drug absorption, distribution, metabolism and excretion.")
    extension: list[dict] | None = Field(None, description="Additional content defined by implementations.")
