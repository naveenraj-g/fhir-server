from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.medication_knowledge.response.codeable_concept import (
    MedicationKnowledgeCodeableConceptResponse,
)
from app.schemas.medication_knowledge.response.quantity import (
    MedicationKnowledgeMoneyResponse,
    MedicationKnowledgeQuantityResponse,
    MedicationKnowledgeRatioResponse,
)
from app.schemas.medication_knowledge.response.reference import (
    PlainMedicationKnowledgeReference,
)


class PlainMedicationKnowledgeRelated(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    type: MedicationKnowledgeCodeableConceptResponse | None = None
    reference: list[PlainMedicationKnowledgeReference] | None = None


class PlainMedicationKnowledgeMonograph(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    type: MedicationKnowledgeCodeableConceptResponse | None = None
    source: PlainMedicationKnowledgeReference | None = None


class PlainMedicationKnowledgeIngredient(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    item_codeable_concept: MedicationKnowledgeCodeableConceptResponse | None = None
    item_reference: PlainMedicationKnowledgeReference | None = None
    is_active: bool | None = None
    strength: MedicationKnowledgeRatioResponse | None = None


class PlainMedicationKnowledgeCost(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    type: MedicationKnowledgeCodeableConceptResponse | None = None
    source: str | None = None
    cost: MedicationKnowledgeMoneyResponse | None = None


class PlainMedicationKnowledgeMonitoringProgram(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    type: MedicationKnowledgeCodeableConceptResponse | None = None
    name: str | None = None


class PlainMedicationKnowledgeAdminGuidelineDosage(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    type: MedicationKnowledgeCodeableConceptResponse | None = None
    dosage: list[dict[str, Any]] | None = None


class PlainMedicationKnowledgeAdminGuidelinePatientChar(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    characteristic_codeable_concept: MedicationKnowledgeCodeableConceptResponse | None = None
    characteristic_quantity: MedicationKnowledgeQuantityResponse | None = None
    value: list[str] | None = None


class PlainMedicationKnowledgeAdminGuideline(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    dosage: list[PlainMedicationKnowledgeAdminGuidelineDosage] | None = None
    indication_codeable_concept: MedicationKnowledgeCodeableConceptResponse | None = None
    indication_reference: PlainMedicationKnowledgeReference | None = None
    patient_characteristics: list[PlainMedicationKnowledgeAdminGuidelinePatientChar] | None = None


class PlainMedicationKnowledgeMedicineClassification(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    type: MedicationKnowledgeCodeableConceptResponse | None = None
    classification: list[MedicationKnowledgeCodeableConceptResponse] | None = None


class PlainMedicationKnowledgePackaging(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: MedicationKnowledgeCodeableConceptResponse | None = None
    quantity: MedicationKnowledgeQuantityResponse | None = None


class PlainMedicationKnowledgeDrugCharacteristic(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    type: MedicationKnowledgeCodeableConceptResponse | None = None
    value_codeable_concept: MedicationKnowledgeCodeableConceptResponse | None = None
    value_string: str | None = None
    value_quantity: MedicationKnowledgeQuantityResponse | None = None
    value_base64_binary: str | None = None


class PlainMedicationKnowledgeRegulatorySubstitution(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    type: MedicationKnowledgeCodeableConceptResponse | None = None
    allowed: bool | None = None


class PlainMedicationKnowledgeRegulatorySchedule(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    schedule: MedicationKnowledgeCodeableConceptResponse | None = None


class PlainMedicationKnowledgeRegulatoryMaxDispense(BaseModel):
    model_config = ConfigDict(extra="allow")

    quantity: MedicationKnowledgeQuantityResponse | None = None
    period: MedicationKnowledgeQuantityResponse | None = None


class PlainMedicationKnowledgeRegulatory(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    regulatory_authority: PlainMedicationKnowledgeReference | None = None
    substitution: list[PlainMedicationKnowledgeRegulatorySubstitution] | None = None
    schedule: list[PlainMedicationKnowledgeRegulatorySchedule] | None = None
    max_dispense: PlainMedicationKnowledgeRegulatoryMaxDispense | None = None


class PlainMedicationKnowledgeKinetics(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    area_under_curve: list[MedicationKnowledgeQuantityResponse] | None = None
    lethal_dose_50: list[MedicationKnowledgeQuantityResponse] | None = None
    half_life_period: MedicationKnowledgeQuantityResponse | None = None
