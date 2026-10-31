from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.consent.enums import (
    ConsentDataMeaning,
    ConsentProvisionType,
)
from app.schemas.consent.input.codeable_concept import (
    ConsentCodeableConceptInput,
    ConsentCodingInput,
)


class ConsentProvisionActorInput(BaseModel):
    """Who|what controlled by this rule (actor)."""

    model_config = ConfigDict(extra="forbid")

    role: ConsentCodeableConceptInput = Field(
        ..., description="How the actor is involved."
    )
    reference: str = Field(
        ...,
        description="Resource for the actor (Device | Group | CareTeam | Organization | Patient | Practitioner | RelatedPerson | PractitionerRole, e.g. 'Practitioner/30001').",
    )
    reference_display: str | None = Field(
        None, description="Plain text display for actor reference."
    )


class ConsentProvisionDataInput(BaseModel):
    """Data controlled by this rule."""

    model_config = ConfigDict(extra="forbid")

    meaning: ConsentDataMeaning = Field(
        ..., description="instance | related | dependents | authoredby."
    )
    reference: str = Field(
        ...,
        description="The actual data reference (e.g. 'Observation/160001').",
    )
    reference_display: str | None = Field(
        None, description="Plain text display for data reference."
    )


class ConsentProvisionInput(BaseModel):
    """Constraints to the base Consent.provision rule."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: ConsentProvisionType | None = Field(
        None, description="deny | permit."
    )
    period_start: datetime | None = Field(
        None, description="Timeframe for this rule (start)."
    )
    period_end: datetime | None = Field(
        None, description="Timeframe for this rule (end)."
    )
    actor: list[ConsentProvisionActorInput] | None = Field(
        None, description="Who|what controlled by this rule."
    )
    action: list[ConsentCodeableConceptInput] | None = Field(
        None, description="Actions controlled by this rule."
    )
    security_label: list[ConsentCodingInput] | None = Field(
        None, description="Security Labels that define affected resources."
    )
    purpose: list[ConsentCodingInput] | None = Field(
        None, description="Context of activities covered by this rule."
    )
    class_: list[ConsentCodingInput] | None = Field(
        None,
        alias="class",
        description="e.g. Resource Type, Profile, or CDA etc.",
    )
    code: list[ConsentCodeableConceptInput] | None = Field(
        None, description="e.g. If code in records, then suit this rule."
    )
    data_period_start: datetime | None = Field(
        None, description="Timeframe for data specified by this rule (start)."
    )
    data_period_end: datetime | None = Field(
        None, description="Timeframe for data specified by this rule (end)."
    )
    data: list[ConsentProvisionDataInput] | None = Field(
        None, description="Data controlled by this rule."
    )
    provision: list["ConsentProvisionInput"] | None = Field(
        None, description="Nested Exception Rules contained within this rule."
    )


ConsentProvisionInput.model_rebuild()
