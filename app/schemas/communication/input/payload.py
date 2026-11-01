from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AttachmentInput
from app.schemas.enums import IdentifierUse


class CommunicationPayloadInput(BaseModel):
    """Communication.payload (0..*) BackboneElement input.

    content[x] choice: content_string | content_attachment | content_reference.
    """

    model_config = ConfigDict(extra="forbid")

    content_string: str | None = Field(
        None, description="Message part content as string."
    )
    content_attachment: AttachmentInput | None = Field(
        None, description="Message part content as Attachment."
    )
    content_reference: str | None = Field(
        None, description="Message part content as Reference string (e.g. 'DocumentReference/320001')."
    )
    content_reference_display: str | None = Field(
        None, description="Display narrative for content reference."
    )
    content_reference_identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier purpose/use."
    )
    content_reference_identifier_type_system: str | None = Field(
        None, description="Fallback identifier type system."
    )
    content_reference_identifier_type_version: str | None = Field(
        None, description="Fallback identifier type version."
    )
    content_reference_identifier_type_code: str | None = Field(
        None, description="Fallback identifier type code."
    )
    content_reference_identifier_type_display: str | None = Field(
        None, description="Fallback identifier type display."
    )
    content_reference_identifier_type_text: str | None = Field(
        None, description="Fallback identifier type text."
    )
    content_reference_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier type user selected."
    )
    content_reference_identifier_system: str | None = Field(
        None, description="Fallback identifier namespace system."
    )
    content_reference_identifier_value: str | None = Field(
        None, description="Fallback identifier value."
    )
    content_reference_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier period start."
    )
    content_reference_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier period end."
    )
