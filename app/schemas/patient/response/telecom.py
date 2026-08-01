from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRContactPoint


class PlainPatientTelecom(BaseModel):
    """Plain-JSON ContactPoint — a contact detail for the patient."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    system: str | None = Field(None, description="phone|fax|email|pager|url|sms|other")
    value: str | None = Field(
        None, description="Contact point details (phone number, email address, etc.)."
    )
    use: str | None = Field(None, description="home|work|temp|old|mobile")
    rank: int | None = Field(
        None, description="Preferred order of use — 1 indicates the most preferred."
    )
    period_start: str | None = Field(
        None, description="ISO 8601 datetime this contact point became valid."
    )
    period_end: str | None = Field(
        None, description="ISO 8601 datetime this contact point stopped being valid."
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


class PatientTelecomListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/telecom."""

    data: list[PlainPatientTelecom] = Field(
        ..., description="Contact point entries for the patient."
    )
    total: int = Field(..., description="Total count of contact point entries.")


class FHIRPatientTelecomListItem(FHIRContactPoint):
    """FHIRContactPoint plus the internal row id, for the GET /{patient_id}/telecom list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientTelecomListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/telecom."""

    data: list[FHIRPatientTelecomListItem] = Field(
        ..., description="Contact point entries for the patient."
    )
    total: int = Field(..., description="Total count of contact point entries.")
