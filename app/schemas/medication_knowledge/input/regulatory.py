from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse
from app.schemas.medication_knowledge.input.codeable_concept import (
    MedicationKnowledgeCodeableConceptInput,
)
from app.schemas.medication_knowledge.input.quantity import (
    MedicationKnowledgeQuantityInput,
)


class MedicationKnowledgeRegulatorySubstitutionInput(BaseModel):
    """MedicationKnowledge.regulatory.substitution (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    type: MedicationKnowledgeCodeableConceptInput = Field(
        ..., description="Specifies the type of substitution allowed."
    )
    allowed: bool = Field(
        ..., description="Specifies if regulation allows for such a substitution."
    )


class MedicationKnowledgeRegulatoryScheduleInput(BaseModel):
    """MedicationKnowledge.regulatory.schedule (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    schedule: MedicationKnowledgeCodeableConceptInput = Field(
        ..., description="Specifies the schedule associated with the medication."
    )


class MedicationKnowledgeRegulatoryMaxDispenseInput(BaseModel):
    """MedicationKnowledge.regulatory.maxDispense (0..1 BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    quantity: MedicationKnowledgeQuantityInput = Field(
        ..., description="The maximum number of units of the medication that can be dispensed in a period."
    )
    period: MedicationKnowledgeQuantityInput | None = Field(
        None, description="The period that applies to the maximum number of units."
    )


class MedicationKnowledgeRegulatoryInput(BaseModel):
    """MedicationKnowledge.regulatory (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    regulatory_authority: str = Field(
        ...,
        description="The authority that is signing the regulatory statement. Reference(Organization).",
    )
    regulatory_authority_display: str | None = Field(None, description="Display text for authority reference.")
    regulatory_authority_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    regulatory_authority_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    regulatory_authority_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    regulatory_authority_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    regulatory_authority_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    regulatory_authority_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    regulatory_authority_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    regulatory_authority_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    regulatory_authority_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    regulatory_authority_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    regulatory_authority_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    substitution: list[MedicationKnowledgeRegulatorySubstitutionInput] | None = Field(
        None, description="Specifies if changes are allowed when dispensing."
    )
    schedule: list[MedicationKnowledgeRegulatoryScheduleInput] | None = Field(
        None, description="Specifies the schedule associated with the medication."
    )
    max_dispense: MedicationKnowledgeRegulatoryMaxDispenseInput | None = Field(
        None, description="The maximum number of units of the medication that can be dispensed."
    )
