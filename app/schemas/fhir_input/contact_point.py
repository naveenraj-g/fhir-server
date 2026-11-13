from pydantic import Field

from app.schemas.enums import ContactPointSystem, ContactPointUse
from app.schemas.fhir_input.base import FhirInputModel
from app.schemas.fhir_input.period import FhirPeriodInput


class FhirContactPointInput(FhirInputModel):
    """FHIR R4 ContactPoint — a phone, fax, email, ... contact detail."""

    system: ContactPointSystem | None = Field(
        None, description="phone | fax | email | pager | url | sms | other."
    )
    value: str | None = Field(
        None, description="The actual contact point details."
    )
    use: ContactPointUse | None = Field(
        None, description="home | work | temp | old | mobile — purpose of this contact point."
    )
    rank: int | None = Field(
        None, ge=1, description="Specify preferred order of use (1 = highest)."
    )
    period: FhirPeriodInput | None = Field(
        None, description="Time period when the contact point was/is in use."
    )
