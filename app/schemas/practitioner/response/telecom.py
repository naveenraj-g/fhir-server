from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRContactPoint


class PlainPractitionerTelecom(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    system: str | None = Field(
        None, description="phone | fax | email | pager | url | sms | other"
    )
    value: str | None = Field(
        None,
        description="The actual contact point details (e.g. a phone number or email address).",
    )
    use: str | None = Field(None, description="home | work | temp | old | mobile")
    rank: int | None = Field(
        None,
        description="Preferred order among a set of contacts — lower values are more preferred.",
    )
    period_start: str | None = Field(None, description="ISO 8601 datetime string.")
    period_end: str | None = Field(None, description="ISO 8601 datetime string.")
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


class PractitionerTelecomListResponse(BaseModel):
    data: list[PlainPractitionerTelecom]
    total: int = Field(..., description="Total count of contact point entries.")


class FHIRPractitionerTelecomListItem(FHIRContactPoint):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerTelecomListResponse(BaseModel):
    data: list[FHIRPractitionerTelecomListItem]
    total: int = Field(..., description="Total count of contact point entries.")
