from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRAddress


class PlainPatientAddress(BaseModel):
    """Plain-JSON Address — a postal or physical address for the patient."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    use: str | None = Field(None, description="home|work|temp|old|billing")
    type: str | None = Field(None, description="postal|physical|both")
    text: str | None = Field(None, description="Full address as a display string.")
    line: list[str] | None = Field(None, description="Street address lines, in order.")
    city: str | None = Field(None, description="Name of city, town, or community.")
    district: str | None = Field(None, description="County or administrative district.")
    state: str | None = Field(
        None, description="Sub-unit of country — state, province, etc."
    )
    postal_code: str | None = Field(None, description="Postal/ZIP code for the area.")
    country: str | None = Field(
        None, description="Country — e.g. an ISO 3166 2- or 3-letter code."
    )
    period_start: str | None = Field(
        None, description="ISO 8601 datetime this address became valid."
    )
    period_end: str | None = Field(
        None, description="ISO 8601 datetime this address stopped being valid."
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


class PatientAddressesListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/addresses."""

    data: list[PlainPatientAddress] = Field(
        ..., description="Address entries for the patient."
    )
    total: int = Field(..., description="Total count of address entries.")


class FHIRPatientAddressListItem(FHIRAddress):
    """FHIRAddress plus the internal row id, for the GET /{patient_id}/addresses list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientAddressesListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/addresses."""

    data: list[FHIRPatientAddressListItem] = Field(
        ..., description="Address entries for the patient."
    )
    total: int = Field(..., description="Total count of address entries.")
