from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ObservationNoteInput(BaseModel):
    """Observation.note (0..* Annotation). Mirrors
    app.schemas.medication_request.input.note.MedicationRequestNoteInput."""

    model_config = ConfigDict(extra="forbid")
    author_string: str | None = Field(None, description="author[x]: string — free-text author.")
    author_reference: str | None = Field(None, description="author[x]: Reference — FHIR reference string.")
    author_reference_display: str | None = Field(None, description="author[x]: Reference — plain text display.")
    time: datetime | None = Field(None, description="When this comment/annotation was made.")
    text: str = Field(..., description="The annotation text (markdown).")
