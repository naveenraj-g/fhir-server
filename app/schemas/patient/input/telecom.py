from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.patient.enums import ContactPointSystem, ContactPointUse


class TelecomCreate(BaseModel):
    """FHIR R4 ContactPoint — a contact detail (phone, email, etc.) for the patient."""

    model_config = ConfigDict(extra="forbid")
    system: ContactPointSystem = Field(
        ...,
        description="Telecommunications form for this contact point. phone|fax|email|pager|url|sms|other.",
    )
    value: str = Field(
        ...,
        description="The actual contact point details (e.g. a phone number or email address).",
    )
    use: ContactPointUse | None = Field(
        None, description="Purpose of this contact point. home|work|temp|old|mobile."
    )
    rank: int | None = Field(
        None,
        ge=1,
        description="Preferred order of use among an individual's contact points — 1 indicates the most preferred.",
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this contact point was/is in use.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this contact point was/is in use.",
    )


class TelecomPatch(BaseModel):
    """Partial update to a contact point — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    system: ContactPointSystem | None = Field(
        None, description="phone|fax|email|pager|url|sms|other."
    )
    value: str | None = Field(
        None, description="Contact point details (phone number, email address, etc.)."
    )
    use: ContactPointUse | None = Field(None, description="home|work|temp|old|mobile.")
    rank: int | None = Field(
        None, ge=1, description="Preferred order — 1 indicates the most preferred."
    )
    period_start: datetime | None = Field(
        None, description="Start of period when this contact point was valid."
    )
    period_end: datetime | None = Field(
        None, description="End of period when this contact point was valid."
    )
