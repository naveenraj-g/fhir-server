from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import AddressType, AddressUse


class PractitionerAddressCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: AddressUse | None = Field(
        None, description="The purpose of this address. home|work|temp|old|billing."
    )
    type: AddressType = Field(
        ...,
        description="Distinguishes between physical addresses (those you can visit) and mailing addresses. postal|physical|both.",
    )
    text: str | None = Field(None, description="Full address as plain text.")
    line: list[str] | None = Field(None, description="Street address lines.")
    city: str = Field(..., description="City, town, or suburb.")
    district: str | None = Field(
        None, description="The name of the administrative area (county)."
    )
    state: str = Field(..., description="State, province, or region.")
    postal_code: str = Field(..., description="Postal or ZIP code.")
    country: str = Field(..., description="Country.")
    period_start: datetime | None = Field(
        None, description="Start of the period during which this address was/is in use."
    )
    period_end: datetime | None = Field(
        None, description="End of the period during which this address was/is in use."
    )


class PractitionerAddressPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: AddressUse | None = None
    type: AddressType | None = None
    text: str | None = None
    line: list[str] | None = None
    city: str | None = None
    district: str | None = Field(
        None, description="The name of the administrative area (county)."
    )
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
