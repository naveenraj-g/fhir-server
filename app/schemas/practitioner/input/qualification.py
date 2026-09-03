from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class QualificationIdentifierCreate(BaseModel):
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
    type_code: str | None = Field(None, description="Code for identifier type.")
    type_display: str | None = Field(None, description="Display for identifier type.")
    type_text: str | None = Field(
        None, description="Plain-text description of identifier type."
    )
    type_user_selected: bool | None = Field(
        None,
        description="Whether this identifier-type coding was chosen directly by the user.",
    )
    system: str = Field(
        ..., description="Namespace URI for the qualification identifier."
    )
    value: str = Field(..., description="Qualification or license number.")
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
        None, description="Display name of the issuing organization."
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


class QualificationIdentifierPatch(BaseModel):
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


class PractitionerQualificationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identifier: list[QualificationIdentifierCreate] | None = Field(
        None, description="Identifiers for this qualification (e.g. license numbers)."
    )
    code_system: str | None = Field(
        None,
        description="Coding system for the qualification type (e.g. http://snomed.info/sct).",
    )
    code_code: str | None = Field(
        None, description="Coded qualification type (e.g. '394814009')."
    )
    code_display: str | None = Field(
        None, description="Display for the qualification code."
    )
    code_text: str | None = Field(
        None,
        description="Human-readable qualification type, e.g. 'MD - Doctor of Medicine'.",
    )
    period_start: datetime | None = Field(
        None, description="Start of the period during which the qualification is valid."
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which the qualification is valid (expiry).",
    )
    issuer: str | None = Field(
        None,
        description="FHIR reference to the issuing organization, e.g. 'Organization/100'.",
    )
    issuer_display: str | None = Field(
        None, description="Display name of the issuing organization."
    )
    issuer_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the issuing organization isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    issuer_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    issuer_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    issuer_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    issuer_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    issuer_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    issuer_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    issuer_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    issuer_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    issuer_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    issuer_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of validity period."
    )


class PractitionerQualificationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identifier: list[QualificationIdentifierPatch] | None = None
    code_system: str | None = None
    code_code: str | None = None
    code_display: str | None = None
    code_text: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    issuer: str | None = Field(
        None, description="FHIR reference, e.g. 'Organization/100'."
    )
    issuer_display: str | None = None
    issuer_identifier_use: IdentifierUse | None = None
    issuer_identifier_type_system: str | None = None
    issuer_identifier_type_version: str | None = None
    issuer_identifier_type_code: str | None = None
    issuer_identifier_type_display: str | None = None
    issuer_identifier_type_text: str | None = None
    issuer_identifier_type_user_selected: bool | None = None
    issuer_identifier_system: str | None = None
    issuer_identifier_value: str | None = None
    issuer_identifier_period_start: datetime | None = None
    issuer_identifier_period_end: datetime | None = None
