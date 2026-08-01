from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.patient.enums import HumanNameUse


class NameCreate(BaseModel):
    """FHIR R4 HumanName — a name associated with the patient."""

    model_config = ConfigDict(extra="forbid")
    use: HumanNameUse | None = Field(
        None,
        description=(
            "Identifies the purpose of this name. "
            "usual|official|temp|nickname|anonymous|old|maiden."
        ),
    )
    text: str | None = Field(
        None,
        description="Text representation of the full name, as it would normally be displayed.",
    )
    family: str | None = Field(
        None, description="Family name (often called 'surname')."
    )
    given: list[str] | None = Field(
        None,
        description="Given names (not always 'first'). Includes middle names — order matters.",
    )
    prefix: list[str] | None = Field(
        None, description="Parts that come before the name (e.g. Mr., Dr., titles)."
    )
    suffix: list[str] | None = Field(
        None,
        description="Parts that come after the name (e.g. Jr., MD, qualifications).",
    )
    period_start: datetime | None = Field(
        None, description="Start of the period during which this name was/is in use."
    )
    period_end: datetime | None = Field(
        None, description="End of the period during which this name was/is in use."
    )


class NamePatch(BaseModel):
    """Partial update to a HumanName entry — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    use: HumanNameUse | None = Field(
        None, description="usual|official|temp|nickname|anonymous|old|maiden."
    )
    text: str | None = Field(None, description="Full name as a display string.")
    family: str | None = Field(None, description="Family (last) name.")
    given: list[str] | None = Field(
        None, description="Given (first/middle) names, in order."
    )
    prefix: list[str] | None = Field(
        None, description="Name prefixes (Mr., Dr., etc.)."
    )
    suffix: list[str] | None = Field(None, description="Name suffixes (Jr., MD, etc.).")
    period_start: datetime | None = Field(
        None, description="Start of period when this name was valid."
    )
    period_end: datetime | None = Field(
        None, description="End of period when this name was valid."
    )
