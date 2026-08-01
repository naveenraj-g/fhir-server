from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import ContactPointSystem, ContactPointUse


class PractitionerTelecomCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: ContactPointSystem = Field(
        ...,
        description="Telecommunications form for this contact point — what communications system is required to make use of it. phone|fax|email|pager|url|sms|other.",
    )
    value: str = Field(
        ..., description="Contact value (phone number, email address, etc.)."
    )
    use: ContactPointUse | None = Field(
        None,
        description="Identifies the purpose for the contact point. home|work|temp|old|mobile.",
    )
    rank: int | None = Field(
        None,
        ge=1,
        description="Specifies a preferred order in which to use a set of contacts. Lower values are more preferred than higher values.",
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this contact point was/is in use.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this contact point was/is in use.",
    )


class PractitionerTelecomPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: ContactPointSystem | None = None
    value: str | None = None
    use: ContactPointUse | None = None
    rank: int | None = Field(None, ge=1)
    period_start: datetime | None = None
    period_end: datetime | None = None
