from sqlalchemy import BigInteger, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirAttachmentMixin, TenantAuditMixin


class CommunicationPayload(FhirAttachmentMixin, TenantAuditMixin, Base):
    """Communication.payload (0..*) BackboneElement child table.
    content[x] can be string, Attachment, or Reference(Resource).
    """

    __tablename__ = "communication_payload"

    _attachment_prefix = "content_attachment_"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
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
    # content_type
    # language
    # data
    # url
    # size
    # hash
    # title
    # creation

    communication = relationship(
        "CommunicationModel", back_populates="payloads"
    )
