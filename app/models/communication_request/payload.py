from sqlalchemy import BigInteger, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirAttachmentMixin, TenantAuditMixin


class CommunicationRequestPayload(
    FhirAttachmentMixin, TenantAuditMixin, Base
):
    """CommunicationRequest.payload (0..*) BackboneElement child table.
    content[x] can be string, Attachment, or Reference(Resource).
    """

    __tablename__ = "communication_request_payload"

    _attachment_prefix = "content_attachment_"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_pk = Column(
        BigInteger,
        ForeignKey("communication_request.id"),
        nullable=False,
        index=True,
    )

    # contentString
    content_string = Column(Text, nullable=True)

    # contentReference
    content_reference_reference = Column(String, nullable=True)
    content_reference_type = Column(String, nullable=True)
    content_reference_id = Column(BigInteger, nullable=True, index=True)
    content_reference_display = Column(String, nullable=True)

    # contentAttachment fields are provided via FhirAttachmentMixin:
    # content_attachment_content_type
    # content_attachment_language
    # content_attachment_data
    # content_attachment_url
    # content_attachment_size
    # content_attachment_hash
    # content_attachment_title
    # content_attachment_creation

    communication_request = relationship(
        "CommunicationRequestModel", back_populates="payloads"
    )
