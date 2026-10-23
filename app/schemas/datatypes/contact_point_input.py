from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import ContactPointSystem, ContactPointUse


class ContactPointInput(BaseModel):
    """A ContactPoint entry (e.g. `telecom[]`) — a contact detail (phone,
    fax, email, ...) for a person or organization. `system`/`value` are
    0..1 per FHIR R4, so they stay optional here; some resources choose to
    require both at the input layer (e.g. LocationTelecomInput,
    HealthcareServiceTelecomInput) by re-declaring just those two fields in
    a subclass."""

    model_config = ConfigDict(extra="forbid")
    system: ContactPointSystem | None = Field(
        None,
        description="Telecommunications form for the contact point — what communications system is required to make use of it: phone|fax|email|pager|url|sms|other.",
    )
    value: str | None = Field(
        None,
        description="The actual contact point details, in a form meaningful to the designated communication system.",
    )
    use: ContactPointUse | None = Field(
        None,
        description="Identifies the purpose for the contact point — home|work|temp|old|mobile.",
    )
    rank: int | None = Field(
        None,
        ge=1,
        description="Specifies a preferred order in which to use a set of contacts. Lower values are more preferred than higher values.",
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the time period when this contact point was/is in use.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the time period when this contact point was/is in use.",
    )
