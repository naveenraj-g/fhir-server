from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse
from app.schemas.medication_knowledge.input.codeable_concept import (
    MedicationKnowledgeCodeableConceptInput,
)
from app.schemas.medication_knowledge.input.quantity import (
    MedicationKnowledgeQuantityInput,
)


class MedicationKnowledgeAdminGuidelineDosageInput(BaseModel):
    """MedicationKnowledge.administrationGuidelines.dosage (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    type: MedicationKnowledgeCodeableConceptInput = Field(
        ..., description="Type of dosage."
    )
    dosage: list[dict[str, Any]] = Field(
        ..., description="Dosage for the medication."
    )


class MedicationKnowledgeAdminGuidelinePatientCharInput(BaseModel):
    """MedicationKnowledge.administrationGuidelines.patientCharacteristics (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    characteristic_codeable_concept: MedicationKnowledgeCodeableConceptInput | None = Field(
        None, description="Categorical characteristic of the patient."
    )
    characteristic_quantity: MedicationKnowledgeQuantityInput | None = Field(
        None, description="Quantitative characteristic of the patient."
    )
    value: list[str] | None = Field(
        None, description="The specific characteristic value."
    )


class MedicationKnowledgeAdminGuidelineInput(BaseModel):
    """MedicationKnowledge.administrationGuidelines (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    dosage: list[MedicationKnowledgeAdminGuidelineDosageInput] | None = Field(
        None, description="Dosage guidelines for different indications."
    )
    indication_codeable_concept: MedicationKnowledgeCodeableConceptInput | None = Field(
        None, description="Indication for use that apply to the guidelines."
    )
    indication_reference: str | None = Field(
        None,
        description="Indication for use reference. Reference(ObservationDefinition).",
    )
    indication_display: str | None = Field(None, description="Display text for indication reference.")
    indication_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    indication_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    indication_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    indication_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    indication_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    indication_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    indication_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    indication_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    indication_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    indication_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    indication_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    patient_characteristics: list[MedicationKnowledgeAdminGuidelinePatientCharInput] | None = Field(
        None, description="Characteristics of the patient that are relevant to the administration guidelines."
    )
