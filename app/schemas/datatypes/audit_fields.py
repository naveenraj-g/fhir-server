from pydantic import BaseModel, ConfigDict, Field


class AuditFields(BaseModel):
    """Shared audit trail fields present on every sub-resource row across
    every resource — not part of FHIR itself, this codebase's own
    created/updated tracking. `created_by`/`updated_by` are plain
    gateway-forwarded input fields for most resources, but come from the
    verified JWT's `sub` for Organization/Location/HealthcareService/
    Patient/Practitioner/PractitionerRole/Schedule/Slot — see CLAUDE.md's
    Multi-Tenancy & Ownership section."""

    model_config = ConfigDict(extra="allow")
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(
        None, description="Acting user who created this row."
    )
    updated_by: str | None = Field(
        None, description="Acting user who last updated this row."
    )
