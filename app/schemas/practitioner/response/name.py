from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRHumanName


class PlainPractitionerName(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    use: str | None = Field(
        None,
        description="usual | official | temp | nickname | anonymous | old | maiden",
    )
    text: str | None = Field(None, description="Full display name.")
    family: str | None = Field(None, description="Family (last) name.")
    given: list[str] | None = Field(None, description="Given (first/middle) names.")
    prefix: list[str] | None = Field(
        None, description="Name prefixes (Mr., Dr., etc.)."
    )
    suffix: list[str] | None = Field(None, description="Name suffixes (Jr., MD, etc.).")
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


class PractitionerNamesListResponse(BaseModel):
    data: list[PlainPractitionerName]
    total: int = Field(..., description="Total count of name entries.")


class FHIRPractitionerNameListItem(FHIRHumanName):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerNamesListResponse(BaseModel):
    data: list[FHIRPractitionerNameListItem]
    total: int = Field(..., description="Total count of name entries.")
