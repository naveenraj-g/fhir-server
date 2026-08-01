from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import HumanNameUse


class PractitionerNameCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: HumanNameUse | None = Field(
        None,
        description="Identifies the purpose for this name. usual|official|temp|nickname|anonymous|old|maiden.",
    )
    text: str | None = Field(None, description="Full name as a display string.")
    family: str | None = Field(None, description="Family (last) name.")
    given: list[str] | None = Field(None, description="Given (first/middle) names.")
    prefix: list[str] | None = Field(
        None, description="Name prefixes (Mr., Dr., etc.)."
    )
    suffix: list[str] | None = Field(None, description="Name suffixes (Jr., MD, etc.).")
    period_start: datetime | None = Field(
        None, description="Start of the period during which this name was valid."
    )
    period_end: datetime | None = Field(
        None, description="End of the period during which this name was valid."
    )


class PractitionerNamePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: HumanNameUse | None = None
    text: str | None = None
    family: str | None = None
    given: list[str] | None = None
    prefix: list[str] | None = None
    suffix: list[str] | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
