from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class CarePlanNoteInput(BaseModel):
    """CarePlan.note / activity.progress (0..* Annotation)."""

    model_config = ConfigDict(extra="forbid")
    author_string: str | None = Field(
        None, description="author[x]: string — free-text author."
    )
    author_reference: str | None = Field(
        None, description="author[x]: Reference — FHIR reference string."
    )
    author_reference_display: str | None = Field(
        None, description="author[x]: Reference — plain text display."
    )
    author_reference_identifier_use: IdentifierUse | None = Field(
        None, description="Purpose of author reference identifier."
    )
    author_reference_identifier_type_system: str | None = Field(
        None, description="Identity of the terminology system for the author reference identifier type."
    )
    author_reference_identifier_type_version: str | None = Field(
        None, description="Version of the system that defines the author reference identifier type."
    )
    author_reference_identifier_type_code: str | None = Field(
        None, description="Symbol in syntax defined by the system for author reference identifier type."
    )
    author_reference_identifier_type_display: str | None = Field(
        None, description="Representation defined by the system for author reference identifier type."
    )
    author_reference_identifier_type_user_selected: bool | None = Field(
        None, description="If this author reference identifier type coding was chosen directly by the user."
    )
    author_reference_identifier_type_text: str | None = Field(
        None, description="Plain text representation of the author reference identifier type."
    )
    author_reference_identifier_system: str | None = Field(
        None, description="The namespace for the author reference identifier value."
    )
    author_reference_identifier_value: str | None = Field(
        None, description="The portion of the author reference identifier typically relevant to the user."
    )
    author_reference_identifier_period_start: datetime | None = Field(
        None, description="Time period when author reference id is/was valid for use - start."
    )
    author_reference_identifier_period_end: datetime | None = Field(
        None, description="Time period when author reference id is/was valid for use - end."
    )
    time: datetime | None = Field(
        None, description="When this comment/annotation was made."
    )
    text: str = Field(..., description="The annotation text (markdown).")
