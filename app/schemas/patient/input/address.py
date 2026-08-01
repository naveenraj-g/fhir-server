from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.patient.enums import AddressType, AddressUse


class AddressCreate(BaseModel):
    """FHIR R4 Address — a postal or physical address for the patient."""

    model_config = ConfigDict(extra="forbid")
    use: AddressUse | None = Field(
        None, description="The purpose of this address. home|work|temp|old|billing."
    )
    type: AddressType | None = Field(
        None,
        description="Distinguishes physical locations from mailing addresses. postal|physical|both.",
    )
    text: str | None = Field(
        None,
        description="Text representation of the address, as it would normally be displayed on a mailing label.",
    )
    line: list[str] | None = Field(
        None,
        description="Street name, number, direction, P.O. Box, or similar — one entry per address line, in order.",
    )
    city: str | None = Field(
        None, description="Name of the city, town, suburb, village, or other community."
    )
    district: str | None = Field(None, description="County or administrative district.")
    state: str | None = Field(
        None, description="Sub-unit of country — state, province, etc."
    )
    postal_code: str | None = Field(None, description="Postal/ZIP code for the area.")
    country: str | None = Field(
        None, description="Country — e.g. an ISO 3166 2- or 3-letter code."
    )
    period_start: datetime | None = Field(
        None, description="Start of the period during which this address was/is in use."
    )
    period_end: datetime | None = Field(
        None, description="End of the period during which this address was/is in use."
    )


class AddressPatch(BaseModel):
    """Partial update to an address — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    use: AddressUse | None = Field(None, description="home|work|temp|old|billing.")
    type: AddressType | None = Field(None, description="postal|physical|both.")
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
    period_start: datetime | None = Field(
        None, description="Start of period when this address was valid."
    )
    period_end: datetime | None = Field(
        None, description="End of period when this address was valid."
    )
