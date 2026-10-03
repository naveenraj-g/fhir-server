from pydantic import BaseModel, ConfigDict, Field


class _AuditFields(BaseModel):
    """Shared audit trail fields present on every Organization sub-resource row
    — not part of FHIR itself, this codebase's own created/updated tracking."""

    model_config = ConfigDict(extra="allow")
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(
        None, description="Acting user who created this row, forwarded by the gateway."
    )
    updated_by: str | None = Field(
        None,
        description="Acting user who last updated this row, forwarded by the gateway.",
    )


class PlainOrganizationCoding(_AuditFields):
    """One entry of a CodeableConcept's `coding[]` — see
    app.schemas.organization.input._shared.OrganizationCodingInput for the
    full reasoning on why this is a real list, not a single flattened
    coding."""

    id: int = Field(..., description="Internal row ID.")
    system: str | None = Field(
        None,
        description="The identification of the code system that defines the meaning of the symbol in the code.",
    )
    version: str | None = Field(
        None,
        description="The version of the code system which was used when choosing this code.",
    )
    code: str | None = Field(None, description="A symbol in syntax defined by the code system.")
    display: str | None = Field(
        None,
        description="A representation of the meaning of the code in the system.",
    )
    user_selected: bool | None = Field(
        None, description="Whether this coding was chosen by a user directly."
    )
