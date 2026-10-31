from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AttachmentInput


class CommunicationRequestPayloadInput(BaseModel):
    """CommunicationRequest.payload (0..*) BackboneElement input.

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
