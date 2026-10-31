from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.document_reference.input.codeable_concept import (
    DocumentReferenceCodeableConceptInput,
)


class DocumentReferenceContextInput(BaseModel):
    """DocumentReference.context (0..1 BackboneElement)."""

    model_config = ConfigDict(extra="forbid")
    encounter: list[str] | None = Field(
        None, description="Context of the document (Encounter or EpisodeOfCare references)."
    )
    event: list[DocumentReferenceCodeableConceptInput] | None = Field(
        None, description="Main clinical acts being documented."
    )
    period_start: datetime | None = Field(
        None, description="Time of service that is being documented (start)."
    )
    period_end: datetime | None = Field(
        None, description="Time of service that is being documented (end)."
    )
    facility_type: DocumentReferenceCodeableConceptInput | None = Field(
        None, description="Kind of organization where admission or service occurred."
    )
    practice_setting: DocumentReferenceCodeableConceptInput | None = Field(
        None, description="Additional details about where the content was created."
    )
    source_patient_info: str | None = Field(
        None, description="Patient demographics from source (Patient reference string)."
    )
    related: list[str] | None = Field(
        None, description="Related identifiers or resources."
    )
