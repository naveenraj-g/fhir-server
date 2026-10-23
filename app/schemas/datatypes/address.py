from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.datatypes.period import FHIRPeriod


class FHIRAddress(BaseModel):
    """FHIR R4 Address — a postal or physical address."""

    use: Optional[str] = Field(None, description="The purpose of this address. home|work|temp|old|billing.")
    type: Optional[str] = Field(
        None, description="Distinguishes physical locations from mailing addresses. postal|physical|both."
    )
    text: Optional[str] = Field(
        None, description="Text representation of the address, as it would normally be displayed on a mailing label."
    )
    line: Optional[List[str]] = Field(
        None, description="Street name, number, direction, P.O. Box, or similar — one entry per address line, in order."
    )
    city: Optional[str] = Field(None, description="Name of the city, town, suburb, village, or other community.")
    district: Optional[str] = Field(None, description="County or administrative district.")
    state: Optional[str] = Field(None, description="Sub-unit of country — state, province, etc.")
    postalCode: Optional[str] = Field(None, description="Postal/ZIP code for the area.")
    country: Optional[str] = Field(None, description="Country — e.g. an ISO 3166 2- or 3-letter code.")
    period: Optional[FHIRPeriod] = Field(
        None, description="The period during which this address was/is in use."
    )
