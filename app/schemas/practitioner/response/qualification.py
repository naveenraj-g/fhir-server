from pydantic import BaseModel, Field

from app.schemas.datatypes import AuditFields, FHIRCodeableConcept, FHIRIdentifier, FHIRPeriod, FHIRReference, PlainCodingRow


class FHIRPractitionerQualification(BaseModel):
    """Practitioner.qualification — FHIR camelCase BackboneElement."""

    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Identifier(s) for this qualification."
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Coded representation of the qualification."
    )
    period: FHIRPeriod | None = Field(
        None, description="Period during which the qualification is valid."
    )
    issuer: FHIRReference | None = Field(
        None, description="Organization that regulates and issues the qualification."
    )


class PlainPractitionerQualificationIdentifier(AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    use: str | None = Field(
        None, description="Identifies the purpose for this identifier, if known."
    )
    type_codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for this identifier's type."
    )
    type_text: str | None = Field(
        None, description="A human language representation of the identifier's type."
    )
    system: str | None = Field(
        None, description="Establishes the namespace for the value."
    )
    value: str | None = Field(
        None,
        description="The portion of the identifier typically relevant to the user, unique within the system.",
    )
    period_start: str | None = Field(
        None,
        description="Start of the time period during which this identifier is/was valid for use.",
    )
    period_end: str | None = Field(
        None,
        description="End of the time period during which this identifier is/was valid for use.",
    )
    assigner_reference: str | None = Field(
        None,
        description="The raw literal reference string as received — independent of whether it resolves locally.",
    )
    assigner: str | None = Field(
        None,
        description="Resolved FHIR reference to the issuing organization, e.g. 'Organization/190001'.",
    )
    assigner_type: str | None = Field(
        None, description="Resolved reference target type (always 'Organization')."
    )
    assigner_id: int | None = Field(
        None, description="Public ID of the resolved assigning Organization, if any."
    )
    assigner_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the assigning organization.",
    )
    assigner_identifier_use: str | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    assigner_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    assigner_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    assigner_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    assigner_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    assigner_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    assigner_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    assigner_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    assigner_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    assigner_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    assigner_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — end of validity period."
    )


class PlainPractitionerQualification(AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    identifiers: list[PlainPractitionerQualificationIdentifier] | None = Field(
        None, description="Identifier(s) for this qualification."
    )
    code_codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for this qualification."
    )
    code_text: str | None = Field(
        None, description="A human language representation of the qualification code."
    )
    period_start: str | None = Field(
        None, description="Start of the period during which the qualification is valid."
    )
    period_end: str | None = Field(
        None, description="End of the period during which the qualification is valid."
    )
    issuer_reference: str | None = Field(
        None,
        description="The raw literal reference string as received — independent of whether it resolves locally.",
    )
    issuer: str | None = Field(
        None,
        description="Resolved FHIR reference to the issuing organization, e.g. 'Organization/190001'.",
    )
    issuer_type: str | None = Field(
        None, description="Resolved reference target type (always 'Organization')."
    )
    issuer_id: int | None = Field(
        None, description="Public ID of the resolved issuing Organization, if any."
    )
    issuer_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the issuing organization.",
    )
    issuer_identifier_use: str | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    issuer_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    issuer_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    issuer_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    issuer_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    issuer_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    issuer_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    issuer_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    issuer_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    issuer_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    issuer_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — end of validity period."
    )
