from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AuditFields, FHIRAttachment, PlainAttachmentRow
from app.schemas.datatypes.reference import FHIRReference


class FHIRCommunicationRequestPayload(BaseModel):
    """FHIR R4 representation of CommunicationRequest.payload BackboneElement.

    content[x] choice: contentString | contentAttachment | contentReference.
    """

    model_config = ConfigDict(populate_by_name=True)

    contentString: str | None = None
    contentAttachment: FHIRAttachment | None = None
    contentReference: FHIRReference | None = None


class PlainCommunicationRequestPayload(AuditFields):
    """Plain snake_case serialization of CommunicationRequest payload child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="DB primary key of this payload row.")
    content_string: str | None = None
    content_attachment: PlainAttachmentRow | None = None
    content_reference_reference: str | None = None
    content_reference: str | None = None
    content_reference_type: str | None = None
    content_reference_id: int | None = None
    content_reference_display: str | None = None
    content_reference_identifier_use: str | None = None
    content_reference_identifier_type_system: str | None = None
    content_reference_identifier_type_version: str | None = None
    content_reference_identifier_type_code: str | None = None
    content_reference_identifier_type_display: str | None = None
    content_reference_identifier_type_text: str | None = None
    content_reference_identifier_type_user_selected: bool | None = None
    content_reference_identifier_system: str | None = None
    content_reference_identifier_value: str | None = None
    content_reference_identifier_period_start: str | None = None
    content_reference_identifier_period_end: str | None = None
