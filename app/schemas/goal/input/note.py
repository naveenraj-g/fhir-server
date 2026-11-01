from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse


class GoalNoteInput(BaseModel):
    """Annotation note for Goal."""

    model_config = ConfigDict(extra="forbid")

    author_string: str | None = Field(
        None, description="Individual responsible for the annotation as a string."
    )
    author_reference: str | None = Field(
        None, description="Individual responsible for the annotation as a reference."
    )
    author_display: str | None = Field(
        None, description="Display name for author reference."
    )
    author_identifier_use: IdentifierUse | None = Field(
        None, description="Purpose of this identifier."
    )
    author_identifier_type_system: str | None = Field(
        None, description="Identity of the terminology system for the identifier type."
    )
    author_identifier_type_version: str | None = Field(
        None, description="Version of the system that defines the identifier type."
    )
    author_identifier_type_code: str | None = Field(
        None, description="Symbol in syntax defined by the system for identifier type."
    )
    author_identifier_type_display: str | None = Field(
        None, description="Representation defined by the system for identifier type."
    )
    author_identifier_type_user_selected: bool | None = Field(
        None, description="If this identifier type coding was chosen directly by the user."
    )
    author_identifier_type_text: str | None = Field(
        None, description="Plain text representation of the identifier type."
    )
    author_identifier_system: str | None = Field(
        None, description="The namespace for the identifier value."
    )
    author_identifier_value: str | None = Field(
        None, description="The portion of the identifier typically relevant to the user."
    )
    author_identifier_period_start: datetime | None = Field(
        None, description="Time period when id is/was valid for use - start."
    )
    author_identifier_period_end: datetime | None = Field(
        None, description="Time period when id is/was valid for use - end."
    )
    time: datetime | None = Field(
        None, description="When the annotation was made."
    )
    text: str = Field(
        ..., description="The annotation text content."
    )
