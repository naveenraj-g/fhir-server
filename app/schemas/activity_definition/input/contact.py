from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import ContactPointInput


class ActivityDefinitionContactInput(BaseModel):
    """ActivityDefinition ContactDetail input (contact, author, editor, reviewer, endorser)."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, description="Name of an individual to contact.")
    telecom: list[ContactPointInput] | None = Field(
        None, description="Contact details for individual or organization."
    )
