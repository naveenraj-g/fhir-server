from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class PractitionerIdentifierCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(
        None,
        description="Identifies the purpose for this identifier, if known. usual|official|temp|secondary|old.",
    )
    type_system: str | None = Field(
        None, description="Coding system for identifier type."
    )
    type_version: str | None = Field(
        None, description="Version of the coding system for identifier type."
    )
    type_code: str | None = Field(
        None, description="Code for identifier type (e.g. NPI, DEA, license)."
    )
    type_display: str | None = Field(None, description="Display for identifier type.")
    type_text: str | None = Field(
        None, description="Plain-text description of identifier type."
    )
    type_user_selected: bool | None = Field(
        None,
        description="Whether this identifier-type coding was chosen directly by the user.",
    )
    system: str = Field(
        ...,
        description="Establishes the namespace for the value (e.g. NPI system) — that is, a URL that describes a set of unique values.",
    )
    value: str = Field(
        ..., description="Identifier value (e.g. NPI number, license number)."
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
        description="Reference(Organization) that issued this identifier, as a FHIR reference string (e.g. 'Organization/100').",
    )
    assigner_display: str | None = Field(
        None, description="Display name of the organization that issued the identifier."
    )
    assigner_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the assigning organization isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    assigner_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    assigner_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    assigner_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
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
        None, description="Fallback identifier — start of validity period."
    )
    assigner_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of validity period."
    )


class PractitionerIdentifierPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = None
    type_system: str | None = None
    type_version: str | None = None
    type_code: str | None = None
    type_display: str | None = None
    type_text: str | None = None
    type_user_selected: bool | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner: str | None = None
    assigner_display: str | None = None
    assigner_identifier_use: IdentifierUse | None = None
    assigner_identifier_type_system: str | None = None
    assigner_identifier_type_version: str | None = None
    assigner_identifier_type_code: str | None = None
    assigner_identifier_type_display: str | None = None
    assigner_identifier_type_text: str | None = None
    assigner_identifier_type_user_selected: bool | None = None
    assigner_identifier_system: str | None = None
    assigner_identifier_value: str | None = None
    assigner_identifier_period_start: datetime | None = None
    assigner_identifier_period_end: datetime | None = None
