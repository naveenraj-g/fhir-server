from pydantic import BaseModel, ConfigDict, Field


class GoalReferenceInput(BaseModel):
    """Reference input for Goal (reference + optional display narrative)."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(
        None, description="FHIR reference string (e.g. 'Condition/120001')."
    )
    display: str | None = Field(
        None, description="Plain text display narrative for reference."
    )
