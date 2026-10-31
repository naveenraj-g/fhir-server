from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProcedureNoteInput(BaseModel):
    """Procedure.note (0..* Annotation)."""

    model_config = ConfigDict(extra="forbid")

    author_string: str | None = Field(
        None, description="author[x]: string — free-text author."
    )
    author_reference: str | None = Field(
        None, description="author[x]: Reference — FHIR reference string (e.g. Practitioner/123)."
    )
    author_reference_display: str | None = Field(
        None, description="author[x]: Reference — plain text display."
    )
    time: datetime | None = Field(
        None, description="When this comment/annotation was made."
    )
    text: str = Field(..., description="The annotation text (markdown).")
