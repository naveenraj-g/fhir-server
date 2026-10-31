from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.consent.input.codeable_concept import ConsentCodeableConceptInput


class ConsentIdentifierInput(BaseModel):
    """Identifier input for Consent."""

    model_config = ConfigDict(extra="forbid")

    use: str | None = Field(
        None, description="usual | official | temp | secondary | old (if known)."
    )
    type: ConsentCodeableConceptInput | None = Field(
        None, description="Description of identifier."
    )
    system: str | None = Field(
        None, description="The namespace for the identifier value."
    )
    value: str | None = Field(None, description="The value that is unique.")
    period_start: datetime | None = Field(
        None, description="Time period when id is/was valid (start)."
    )
    period_end: datetime | None = Field(
        None, description="Time period when id is/was valid (end)."
    )
    assigner: str | None = Field(
        None,
        description="Organization that issued id (e.g. 'Organization/190001').",
    )
    assigner_display: str | None = Field(
        None, description="Display name for assigner reference."
    )
