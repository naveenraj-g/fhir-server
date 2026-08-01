from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse


class IdentifierCreate(BaseModel):
    """FHIR R4 Identifier — a business identifier for this patient (e.g. MRN, SSN, passport)."""

    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(
        None,
        description=(
            "The purpose of this identifier. usual|official|temp|secondary|old."
        ),
    )
    type_system: str | None = Field(
        None,
        description=(
            "Identifier.type.coding.system — coding system that defines the "
            "identifier type (e.g. http://terminology.hl7.org/CodeSystem/v2-0203)."
        ),
    )
    type_version: str | None = Field(
        None,
        description="Identifier.type.coding.version — version of the identifier-type coding system.",
    )
    type_code: str | None = Field(
        None,
        description="Identifier.type.coding.code — code for the identifier type (e.g. MR, SS, PPN).",
    )
    type_display: str | None = Field(
        None,
        description="Identifier.type.coding.display — human-readable display for the identifier-type code.",
    )
    type_text: str | None = Field(
        None,
        description="Identifier.type.text — plain-text rendering of the identifier-type CodeableConcept.",
    )
    type_user_selected: bool | None = Field(
        None,
        description="Identifier.type.coding.userSelected — whether this identifier-type coding was chosen directly by the user.",
    )
    system: str = Field(
        ...,
        description="The namespace (a URI) that identifies the scope this identifier's value is unique within.",
    )
    value: str = Field(
        ..., description="The identifier value itself, unique within the given system."
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this identifier is/was valid for use.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this identifier is/was valid for use.",
    )
    assigner: str | None = Field(
        None,
        description=(
            "Identifier.assigner — Reference(Organization) that issued this "
            "identifier, as a FHIR reference string (e.g. 'Organization/100')."
        ),
    )
    assigner_display: str | None = Field(
        None, description="Display text for the assigning organization."
    )
    assigner_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the assigning organization "
        "isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    assigner_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    assigner_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    assigner_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    assigner_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    assigner_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    assigner_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    assigner_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    assigner_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    assigner_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — when it became valid."
    )
    assigner_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — when it stopped being valid."
    )


class IdentifierPatch(BaseModel):
    """Partial update to a business identifier — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(
        None, description="usual|official|temp|secondary|old."
    )
    type_system: str | None = Field(
        None, description="Coding system for identifier type."
    )
    type_version: str | None = Field(
        None, description="Version of the coding system for identifier type."
    )
    type_code: str | None = Field(
        None, description="Code for identifier type (e.g. MR, SS)."
    )
    type_display: str | None = Field(None, description="Display for identifier type.")
    type_text: str | None = Field(
        None, description="Text of the CodeableConcept for identifier type."
    )
    type_user_selected: bool | None = Field(
        None, description="Whether this coding was chosen directly by the user."
    )
    system: str | None = Field(None, description="URI namespace of the identifier.")
    value: str | None = Field(
        None, description="Identifier value within the given system."
    )
    period_start: datetime | None = Field(
        None, description="Start of identifier validity period."
    )
    period_end: datetime | None = Field(
        None, description="End of identifier validity period."
    )
    assigner: str | None = Field(
        None,
        description="Reference(Organization) that issued this identifier, as a "
        "FHIR reference string (e.g. 'Organization/100').",
    )
    assigner_display: str | None = Field(
        None, description="Display text for the assigning organization."
    )
    assigner_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the assigning organization "
        "isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    assigner_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    assigner_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    assigner_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    assigner_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    assigner_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    assigner_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    assigner_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    assigner_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    assigner_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — when it became valid."
    )
    assigner_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — when it stopped being valid."
    )
