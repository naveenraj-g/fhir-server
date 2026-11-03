from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRMeta
from app.schemas.medication_knowledge.response.codeable_concept import (
    MedicationKnowledgeCodeableConceptResponse,
)
from app.schemas.medication_knowledge.response.quantity import (
    MedicationKnowledgeQuantityResponse,
)
from app.schemas.medication_knowledge.response.reference import (
    PlainMedicationKnowledgeReference,
)
from app.schemas.medication_knowledge.response.sub_resources import (
    PlainMedicationKnowledgeAdminGuideline,
    PlainMedicationKnowledgeCost,
    PlainMedicationKnowledgeDrugCharacteristic,
    PlainMedicationKnowledgeIngredient,
    PlainMedicationKnowledgeKinetics,
    PlainMedicationKnowledgeMedicineClassification,
    PlainMedicationKnowledgeMonitoringProgram,
    PlainMedicationKnowledgeMonograph,
    PlainMedicationKnowledgePackaging,
    PlainMedicationKnowledgeRegulatory,
    PlainMedicationKnowledgeRelated,
)


class FHIRMedicationKnowledgeSchema(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    resourceType: Literal["MedicationKnowledge"] = "MedicationKnowledge"
    id: str | None = None
    meta: FHIRMeta | None = None
    extension: list[dict[str, Any]] | None = None

    code: dict[str, Any] | None = None
    status: str | None = None
    manufacturer: dict[str, Any] | None = None
    doseForm: dict[str, Any] | None = None
    amount: dict[str, Any] | None = None
    synonym: list[str] | None = None
    relatedMedicationKnowledge: list[dict[str, Any]] | None = None
    associatedMedication: list[dict[str, Any]] | None = None
    productType: list[dict[str, Any]] | None = None
    monograph: list[dict[str, Any]] | None = None
    ingredient: list[dict[str, Any]] | None = None
    preparationInstruction: str | None = None
    intendedRoute: list[dict[str, Any]] | None = None
    cost: list[dict[str, Any]] | None = None
    monitoringProgram: list[dict[str, Any]] | None = None
    administrationGuidelines: list[dict[str, Any]] | None = None
    medicineClassification: list[dict[str, Any]] | None = None
    packaging: dict[str, Any] | None = None
    drugCharacteristic: list[dict[str, Any]] | None = None
    contraindication: list[dict[str, Any]] | None = None
    regulatory: list[dict[str, Any]] | None = None
    kinetics: list[dict[str, Any]] | None = None


class PlainMedicationKnowledgeResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    extension: list[dict[str, Any]] | None = None

    code: MedicationKnowledgeCodeableConceptResponse | None = None
    status: str | None = None
    manufacturer: PlainMedicationKnowledgeReference | None = None
    dose_form: MedicationKnowledgeCodeableConceptResponse | None = None
    amount: MedicationKnowledgeQuantityResponse | None = None
    synonym: list[str] | None = None
    related_medication_knowledge: list[PlainMedicationKnowledgeRelated] | None = None
    associated_medication: list[PlainMedicationKnowledgeReference] | None = None
    product_type: list[MedicationKnowledgeCodeableConceptResponse] | None = None
    monograph: list[PlainMedicationKnowledgeMonograph] | None = None
    ingredient: list[PlainMedicationKnowledgeIngredient] | None = None
    preparation_instruction: str | None = None
    intended_route: list[MedicationKnowledgeCodeableConceptResponse] | None = None
    cost: list[PlainMedicationKnowledgeCost] | None = None
    monitoring_program: list[PlainMedicationKnowledgeMonitoringProgram] | None = None
    administration_guidelines: list[PlainMedicationKnowledgeAdminGuideline] | None = None
    medicine_classification: list[PlainMedicationKnowledgeMedicineClassification] | None = None
    packaging: PlainMedicationKnowledgePackaging | None = None
    drug_characteristic: list[PlainMedicationKnowledgeDrugCharacteristic] | None = None
    contraindication: list[PlainMedicationKnowledgeReference] | None = None
    regulatory: list[PlainMedicationKnowledgeRegulatory] | None = None
    kinetics: list[PlainMedicationKnowledgeKinetics] | None = None


class PaginatedMedicationKnowledgeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(..., description="Total number of resources matching the query.")
    limit: int = Field(..., description="Page size.")
    offset: int = Field(..., description="Offset.")
    data: list[PlainMedicationKnowledgeResponse] = Field(..., description="List of medications in plain format.")


class FHIRMedicationKnowledgeBundleEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = None
    resource: FHIRMedicationKnowledgeSchema


class FHIRMedicationKnowledgeBundle(BaseModel):
    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int = Field(..., description="Total matching resources.")
    entry: list[FHIRMedicationKnowledgeBundleEntry] = Field(default_factory=list)
