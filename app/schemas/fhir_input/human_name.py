from pydantic import Field

from app.schemas.enums import HumanNameUse
from app.schemas.fhir_input.base import FhirInputModel
from app.schemas.fhir_input.period import FhirPeriodInput


class FhirHumanNameInput(FhirInputModel):
    """FHIR R4 HumanName — a name associated with a person."""

    use: HumanNameUse | None = Field(
        None,
        description="usual | official | temp | nickname | anonymous | old | maiden.",
    )
    text: str | None = Field(
        None, description="Text representation of the full name."
    )
    family: str | None = Field(
        None, description="Family name (often called 'Surname')."
    )
    given: list[str] | None = Field(
        None, description="Given names (not always 'first'). Includes middle names."
    )
    prefix: list[str] | None = Field(
        None, description="Parts that come before the name."
    )
    suffix: list[str] | None = Field(
        None, description="Parts that come after the name."
    )
    period: FhirPeriodInput | None = Field(
        None, description="Time period when name was/is in use."
    )
