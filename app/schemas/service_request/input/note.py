from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServiceRequestNoteInput(BaseModel):
    """ServiceRequest.note (0..* Annotation) —
    https://www.hl7.org/fhir/R4/datatypes.html#Annotation

    `author[x]` (0..1, choice of Reference(Practitioner|Patient|
    RelatedPerson|Organization) | string) — exactly one of
    `author_string`/`author_reference` should be supplied; no identifier
    fallback for this minor choice-type variant (same scope decision as
    Questionnaire.item.initial's own value_reference)."""

    model_config = ConfigDict(extra="forbid")
    author_string: str | None = Field(None, description="author[x]: string — free-text author.")
    author_reference: str | None = Field(None, description="author[x]: Reference — FHIR reference string.")
    author_reference_display: str | None = Field(None, description="author[x]: Reference — plain text display.")
    time: datetime | None = Field(None, description="When this comment/annotation was made.")
    text: str = Field(..., description="The annotation text (markdown).")
