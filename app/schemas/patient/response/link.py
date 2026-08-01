from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRReference


class FHIRPatientLink(BaseModel):
    """FHIR R4 Patient.link — a link to another Patient or RelatedPerson resource
    that concerns the same actual person."""

    other: FHIRReference = Field(
        ...,
        description="The other patient or related person resource that this link refers to.",
    )
    type: str = Field(..., description="replaced-by|replaces|refer|seealso")


class PlainPatientLink(BaseModel):
    """Plain-JSON Patient.link — a link to another Patient or RelatedPerson
    resource that concerns the same actual person."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    other_type: str | None = Field(None, description="Patient|RelatedPerson")
    other_id: int | None = Field(
        None, description="Public id of the linked Patient/RelatedPerson resource."
    )
    other_display: str | None = Field(
        None, description="Display text for the linked resource."
    )
    other_identifier_use: str | None = Field(
        None,
        description="Fallback identifier (used when the linked resource isn't "
        "in this system) — usual|official|temp|secondary|old.",
    )
    other_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    other_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    other_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    other_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    other_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    other_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    other_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    other_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    other_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    other_identifier_period_end: str | None = Field(
        None,
        description="Fallback identifier — ISO 8601 datetime it stopped being valid.",
    )
    type: str | None = Field(None, description="replaced-by|replaces|refer|seealso")
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


class PatientLinksListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/links."""

    data: list[PlainPatientLink] = Field(..., description="Patient link entries.")
    total: int = Field(..., description="Total count of patient link entries.")


class FHIRPatientLinkListItem(FHIRPatientLink):
    """FHIRPatientLink plus the internal row id, for the GET /{patient_id}/links list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientLinksListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/links."""

    data: list[FHIRPatientLinkListItem] = Field(
        ..., description="Patient link entries."
    )
    total: int = Field(..., description="Total count of patient link entries.")
