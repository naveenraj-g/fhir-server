from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRIdentifier


class PlainPractitionerIdentifier(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
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
    type_code: str | None = Field(
        None, description="Identifier type code (e.g. NPI, DEA)."
    )
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
        None, description="Namespace URI for the identifier value."
    )
    value: str | None = Field(None, description="The identifier value.")
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


class PractitionerIdentifiersListResponse(BaseModel):
    data: list[PlainPractitionerIdentifier]
    total: int = Field(..., description="Total count of identifier entries.")


class FHIRPractitionerIdentifierListItem(FHIRIdentifier):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerIdentifiersListResponse(BaseModel):
    data: list[FHIRPractitionerIdentifierListItem]
    total: int = Field(..., description="Total count of identifier entries.")
