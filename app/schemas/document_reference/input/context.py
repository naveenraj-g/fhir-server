from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.document_reference.input.codeable_concept import (
    DocumentReferenceCodeableConceptInput,
)
from app.schemas.document_reference.input.reference import (
    DocumentReferenceReferenceInput,
)
from app.schemas.enums import IdentifierUse


class DocumentReferenceContextInput(BaseModel):
    """DocumentReference.context (0..1 BackboneElement)."""

    model_config = ConfigDict(extra="forbid")
    encounter: list[DocumentReferenceReferenceInput | str] | None = Field(
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
    source_patient_info_display: str | None = Field(
        None, description="Display text for source patient info."
    )
    source_patient_info_identifier_use: IdentifierUse | None = Field(None)
    source_patient_info_identifier_type_system: str | None = Field(None)
    source_patient_info_identifier_type_version: str | None = Field(None)
    source_patient_info_identifier_type_code: str | None = Field(None)
    source_patient_info_identifier_type_display: str | None = Field(None)
    source_patient_info_identifier_type_user_selected: bool | None = Field(None)
    source_patient_info_identifier_type_text: str | None = Field(None)
    source_patient_info_identifier_system: str | None = Field(None)
    source_patient_info_identifier_value: str | None = Field(None)
    source_patient_info_identifier_period_start: datetime | None = Field(None)
    source_patient_info_identifier_period_end: datetime | None = Field(None)

    related: list[DocumentReferenceReferenceInput | str] | None = Field(
        None, description="Related identifiers or resources."
    )
