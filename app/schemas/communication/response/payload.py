from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AuditFields, FHIRAttachment, PlainAttachmentRow
from app.schemas.datatypes.reference import FHIRReference


class FHIRCommunicationPayload(BaseModel):
    """FHIR R4 representation of Communication.payload BackboneElement.

    content[x] choice: contentString | contentAttachment | contentReference.
    """

    model_config = ConfigDict(populate_by_name=True)

    contentString: str | None = None
    contentAttachment: FHIRAttachment | None = None
    contentReference: FHIRReference | None = None


class PlainCommunicationPayload(AuditFields):
    """Plain snake_case serialization of Communication payload child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="DB primary key of this payload row.")
    content_string: str | None = None
    content_attachment: PlainAttachmentRow | None = None
    content_reference: str | None = None
    content_reference_type: str | None = None
    content_reference_id: int | None = None
    content_reference_display: str | None = None
