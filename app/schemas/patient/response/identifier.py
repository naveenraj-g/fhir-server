from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRIdentifier


class PlainPatientIdentifier(BaseModel):
    """Plain-JSON Identifier — a business identifier for this patient."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    use: str | None = Field(None, description="usual|official|temp|secondary|old")
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
    period_start: str | None = Field(
        None, description="ISO 8601 datetime this identifier became valid."
    )
    period_end: str | None = Field(
        None, description="ISO 8601 datetime this identifier stopped being valid."
    )
    assigner_type: str | None = Field(
        None, description="Reference type for the assigning organization."
    )
    assigner_id: int | None = Field(
        None, description="Public id of the assigning Organization."
    )
    assigner_display: str | None = Field(
        None, description="Display text for the assigning organization."
    )
    assigner_identifier_use: str | None = Field(
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


class PatientIdentifiersListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/identifiers."""

    data: list[PlainPatientIdentifier] = Field(
        ..., description="Business identifier entries for the patient."
    )
    total: int = Field(..., description="Total count of identifier entries.")


class FHIRPatientIdentifierListItem(FHIRIdentifier):
    """FHIRIdentifier plus the internal row id, for the GET /{patient_id}/identifiers list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientIdentifiersListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/identifiers."""

    data: list[FHIRPatientIdentifierListItem] = Field(
        ..., description="Business identifier entries for the patient."
    )
    total: int = Field(..., description="Total count of identifier entries.")
