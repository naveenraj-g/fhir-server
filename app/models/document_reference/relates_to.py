from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.document_reference.enums import (
    DocumentReferenceTargetReferenceType,
    DocumentRelationshipType,
)
from app.models.enums import IdentifierUse
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
    target_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    target_identifier_type_system = Column(String, nullable=True)
    target_identifier_type_version = Column(String, nullable=True)
    target_identifier_type_code = Column(String, nullable=True)
    target_identifier_type_display = Column(String, nullable=True)
    target_identifier_type_user_selected = Column(Boolean, nullable=True)
    target_identifier_type_text = Column(String, nullable=True)
    target_identifier_system = Column(String, nullable=True)
    target_identifier_value = Column(String, nullable=True)
    target_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    target_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    document_reference = relationship("DocumentReferenceModel", back_populates="relates_to")
