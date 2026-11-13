from pydantic import Field

from app.schemas.enums import AddressType, AddressUse
from app.schemas.fhir_input.base import FhirInputModel
from app.schemas.fhir_input.period import FhirPeriodInput


class FhirAddressInput(FhirInputModel):
    """FHIR R4 Address — a postal or physical address."""

    use: AddressUse | None = Field(
        None, description="home | work | temp | old | billing — purpose of this address."
    )
    type: AddressType | None = Field(
        None, description="postal | physical | both."
    )
    text: str | None = Field(
        None, description="Text representation of the address."
    )
    line: list[str] | None = Field(
        None,
        description="Street name, number, direction & P.O. Box etc. — one entry per line, in order.",
    )
    city: str | None = Field(
        None, description="Name of city, town etc."
    )
    district: str | None = Field(None, description="District name (aka county).")
    state: str | None = Field(
        None, description="Sub-unit of country (abbreviations ok)."
    )
    postalCode: str | None = Field(None, description="Postal code for area.")
    country: str | None = Field(
        None, description="Country (e.g. can be ISO 3166 2 or 3 letter code)."
    )
    period: FhirPeriodInput | None = Field(
        None, description="Time period when the address was/is in use."
    )
