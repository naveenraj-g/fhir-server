from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.document_reference.enums import (
    DocumentReferenceTargetReferenceType,
    DocumentRelationshipType,
)
from app.models.shared import TenantAuditMixin


class DocumentReferenceRelatesTo(TenantAuditMixin, Base):
    """DocumentReference.relatesTo (0..*) child table."""

    __tablename__ = "document_reference_relates_to"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )

    code = Column(
        Enum(
            DocumentRelationshipType,
            name="document_relationship_type",
        ),
        nullable=False,
    )
    target_reference = Column(String, nullable=True)
    target_type = Column(
        Enum(
            DocumentReferenceTargetReferenceType,
            name="document_reference_target_reference_type",
        ),
        nullable=True,
    )
    target_id = Column(BigInteger, nullable=True, index=True)
    target_display = Column(String, nullable=True)

    document_reference = relationship("DocumentReferenceModel", back_populates="relates_to")
