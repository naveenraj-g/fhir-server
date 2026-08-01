from pydantic import BaseModel, Field

from app.schemas.common.fhir import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRPeriod,
    FHIRReference,
)


class FHIRQualification(BaseModel):
    identifier: list[FHIRIdentifier] | None = None
    code: FHIRCodeableConcept | None = Field(
        None, description="Coded qualification type."
    )
    status: FHIRCodeableConcept | None = Field(
        None,
        description="Status of the qualification (e.g. active, inactive, pending).",
    )
    period: FHIRPeriod | None = Field(
        None, description="Qualification validity period."
    )
    issuer: FHIRReference | None = Field(
        None, description="Issuing organization reference."
    )


class PlainQualificationIdentifier(BaseModel):
    id: int = Field(..., description="Internal row ID.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    use: str | None = Field(
        None, description="usual | official | temp | secondary | old"
    )
    type_system: str | None = Field(
        None, description="Coding system URI for identifier type."
    )
    type_version: str | None = Field(
        None, description="Version of the coding system for identifier type."
    )
    type_code: str | None = Field(None, description="Identifier type code.")
    type_display: str | None = Field(
        None, description="Human-readable identifier type."
    )
    type_text: str | None = Field(
        None, description="Plain-text description of identifier type."
    )
    type_user_selected: bool | None = Field(
        None,
        description="Whether this identifier-type coding was chosen directly by the user.",
    )
    system: str | None = Field(
        None, description="Namespace URI for the qualification identifier."
    )
    value: str | None = Field(None, description="Qualification or license number.")
    period_start: str | None = Field(None, description="ISO 8601 datetime string.")
    period_end: str | None = Field(None, description="ISO 8601 datetime string.")
    assigner_type: str | None = Field(
        None, description="Reference type for the assigning organization."
    )
    assigner_id: int | None = Field(
        None, description="Public id of the assigning Organization."
    )
    assigner_display: str | None = Field(
        None, description="Display name of the issuing organization."
    )
    assigner_identifier_use: str | None = Field(
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
    assigner_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    assigner_identifier_period_end: str | None = Field(
        None,
        description="Fallback identifier — ISO 8601 datetime it stopped being valid.",
    )
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this row."
    )
    updated_by: str | None = Field(
        None, description="Acting-user value recorded as the last updater of this row."
    )


class PlainQualification(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    identifier: list[PlainQualificationIdentifier] | None = Field(
        None, description="Identifiers for this qualification (e.g. license numbers)."
    )
    code_system: str | None = Field(
        None, description="Coding system URI for qualification type."
    )
    code_code: str | None = Field(None, description="Coded qualification type.")
    code_display: str | None = Field(
        None, description="Display for the qualification code."
    )
    code_text: str | None = Field(
        None, description="Human-readable qualification type."
    )
    status_system: str | None = Field(
        None, description="Coding system URI for qualification status."
    )
    status_code: str | None = Field(
        None, description="Status code (e.g. active, inactive, pending)."
    )
    status_display: str | None = Field(None, description="Display for the status code.")
    status_text: str | None = Field(
        None, description="Human-readable qualification status."
    )
    period_start: str | None = Field(None, description="ISO 8601 datetime string.")
    period_end: str | None = Field(
        None, description="ISO 8601 datetime string — qualification expiry."
    )
    issuer_type: str | None = Field(
        None, description="Reference type for issuer, always 'Organization'."
    )
    issuer_id: int | None = Field(
        None, description="Public Organization ID that issued the qualification."
    )
    issuer_display: str | None = Field(
        None, description="Display name of the issuing organization."
    )
    issuer_identifier_use: str | None = Field(
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
    issuer_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    issuer_identifier_period_end: str | None = Field(
        None,
        description="Fallback identifier — ISO 8601 datetime it stopped being valid.",
    )
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this row."
    )
    updated_by: str | None = Field(
        None, description="Acting-user value recorded as the last updater of this row."
    )


class PractitionerQualificationsListResponse(BaseModel):
    data: list[PlainQualification]
    total: int = Field(..., description="Total count of qualification entries.")


class FHIRPractitionerQualificationListItem(FHIRQualification):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerQualificationsListResponse(BaseModel):
    data: list[FHIRPractitionerQualificationListItem]
    total: int = Field(..., description="Total count of qualification entries.")
