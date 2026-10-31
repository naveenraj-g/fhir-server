from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class DocumentReferenceSecurityLabel(TenantAuditMixin, Base):
    """DocumentReference.securityLabel (0..*) child table."""

    __tablename__ = "document_reference_security_label"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    document_reference = relationship("DocumentReferenceModel", back_populates="security_labels")
    codings = relationship(
        "DocumentReferenceSecurityLabelCoding",
        back_populates="security_label",
        cascade="all, delete-orphan",
    )


class DocumentReferenceSecurityLabelCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of DocumentReference.securityLabel.coding (0..*)."""

    __tablename__ = "document_reference_security_label_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_security_label_id = Column(
        BigInteger,
        ForeignKey("document_reference_security_label.id"),
        nullable=False,
        index=True,
    )

    security_label = relationship("DocumentReferenceSecurityLabel", back_populates="codings")
