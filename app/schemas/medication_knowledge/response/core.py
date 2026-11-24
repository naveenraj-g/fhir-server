from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRMeta,
    FHIRQuantity,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRMedicationKnowledgeRelated(BaseModel):
    type: FHIRCodeableConcept | None = Field(
        None, description="Category of medicationKnowledge."
    )
    reference: list[FHIRReference] | None = Field(
        None, description="Associated documentation (MedicationKnowledge)."
    )


class FHIRMedicationKnowledgeMonograph(BaseModel):
    type: FHIRCodeableConcept | None = Field(
        None, description="The category of medication document."
    )
    source: FHIRReference | None = Field(
        None, description="Associated documentation (DocumentReference or Media)."
    )


class FHIRMedicationKnowledgeIngredient(BaseModel):
    itemCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="The ingredient (CodeableConcept)."
    )
    itemReference: FHIRReference | None = Field(
        None, description="The ingredient (Substance)."
    )
    isActive: bool | None = Field(None, description="Active ingredient indicator.")
    strength: dict | None = Field(
        None, description="Quantity of ingredient present (a Ratio)."
    )


class FHIRMedicationKnowledgeCost(BaseModel):
    type: FHIRCodeableConcept | None = Field(
        None, description="The category of the cost information."
    )
    source: str | None = Field(
        None, description="The source or owner for the price information."
    )
    cost: dict | None = Field(
        None, description="The price of the medication (a Money)."
    )


class FHIRMedicationKnowledgeMonitoringProgram(BaseModel):
    type: FHIRCodeableConcept | None = Field(None, description="Type of program.")
    name: str | None = Field(None, description="Name of the reviewing program.")


class FHIRMedicationKnowledgeMedicineClassification(BaseModel):
    type: FHIRCodeableConcept | None = Field(
        None, description="The type of category for the medication."
    )
    classification: list[FHIRCodeableConcept] | None = Field(
        None, description="Specific category assigned to the medication."
    )


class FHIRMedicationKnowledgeSchema(BaseModel):
    resourceType: str = Field(
        "MedicationKnowledge", description="Always 'MedicationKnowledge'."
    )
    id: str = Field(..., description="Public medication_knowledge_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Code that identifies this medication."
    )
    status: str | None = Field(
        None, description="active | inactive | entered-in-error."
    )
    manufacturer: FHIRReference | None = Field(
        None, description="Manufacturer of the item."
    )
    doseForm: FHIRCodeableConcept | None = Field(
        None, description="powder | tablets | capsule ..."
    )
    amount: FHIRQuantity | None = Field(None, description="Amount of drug in package.")
    synonym: list[str] | None = Field(
        None, description="Additional names for a medication."
    )
    relatedMedicationKnowledge: list[FHIRMedicationKnowledgeRelated] | None = Field(
        None, description="Associated or related medication information."
    )
    associatedMedication: list[FHIRReference] | None = Field(
        None,
        description="A medication resource that is associated with this medication.",
    )
    productType: list[FHIRCodeableConcept] | None = Field(
        None, description="Category of the medication or product."
    )
    monograph: list[FHIRMedicationKnowledgeMonograph] | None = Field(
        None, description="Associated documentation about the medication."
    )
    ingredient: list[FHIRMedicationKnowledgeIngredient] | None = Field(
        None, description="Active or inactive ingredient."
    )
    preparationInstruction: str | None = Field(
        None, description="The instructions for preparing the medication."
    )
    intendedRoute: list[FHIRCodeableConcept] | None = Field(
        None, description="The intended or approved route of administration."
    )
    cost: list[FHIRMedicationKnowledgeCost] | None = Field(
        None, description="The pricing of the drug."
    )
    monitoringProgram: list[FHIRMedicationKnowledgeMonitoringProgram] | None = Field(
        None, description="Program under which a medication is reviewed."
    )
    administrationGuidelines: list[dict] | None = Field(
        None, description="Guidelines for the administration of the medication."
    )
    medicineClassification: (
        list[FHIRMedicationKnowledgeMedicineClassification] | None
    ) = Field(None, description="Categorization of the medication.")
    packaging: dict | None = Field(
        None, description="Details about packaged medications."
    )
    drugCharacteristic: list[dict] | None = Field(
        None, description="Specifies descriptive properties of the medicine."
    )
    contraindication: list[FHIRReference] | None = Field(
        None, description="Potential clinical issue with or between medication(s)."
    )
    regulatory: list[dict] | None = Field(
        None, description="Regulatory information about a medication."
    )
    kinetics: list[dict] | None = Field(
        None,
        description="The time course of drug absorption, distribution, metabolism and excretion.",
    )


class FHIRMedicationKnowledgeBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRMedicationKnowledgeSchema | dict = Field(
        ...,
        description="A MedicationKnowledge (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Organization / DocumentReference (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRMedicationKnowledgeBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRMedicationKnowledgeBundleEntry] | None = None
