from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes.fhir_attachment import FhirAttachmentMixin


class DocumentReferenceContent(FhirAttachmentMixin, TenantAuditMixin, Base):
    """DocumentReference.content (1..*) child table.
    Embeds Attachment (prefixed with attachment_) and format (0..1 Coding).
    """

    __tablename__ = "document_reference_content"

    _attachment_prefix = "attachment_"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )

    # format (0..1 Coding)
    format_system = Column(String, nullable=True)
    format_version = Column(String, nullable=True)
    format_code = Column(String, nullable=True)
    format_display = Column(String, nullable=True)
    format_user_selected = Column(Boolean, nullable=True)

    document_reference = relationship("DocumentReferenceModel", back_populates="contents")
