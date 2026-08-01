from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRAddress


class PlainPractitionerAddress(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    use: str | None = Field(None, description="home | work | temp | old | billing")
    type: str | None = Field(None, description="postal | physical | both")
    text: str | None = Field(
        None,
        description="The entire address as it should be displayed, e.g. on a postal label.",
    )
    line: list[str] | None = Field(
        None,
        description="House number, apartment number, street name, and similar information.",
    )
    city: str | None = Field(
        None,
        description="The name of the city, town, suburb, village or other community.",
    )
    district: str | None = Field(
        None, description="The name of the administrative area (county)."
    )
    state: str | None = Field(
        None,
        description="Sub-unit of a country with limited sovereignty in a federally organized country.",
    )
    postal_code: str | None = Field(
        None,
        description="A postal code designating a region defined by the postal service.",
    )
    country: str | None = Field(
        None,
        description="Country — a nation as commonly understood or generally accepted.",
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


class PractitionerAddressesListResponse(BaseModel):
    data: list[PlainPractitionerAddress]
    total: int = Field(..., description="Total count of address entries.")


class FHIRPractitionerAddressListItem(FHIRAddress):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerAddressesListResponse(BaseModel):
    data: list[FHIRPractitionerAddressListItem]
    total: int = Field(..., description="Total count of address entries.")
