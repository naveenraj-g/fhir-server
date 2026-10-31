from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class DocumentReferenceCategory(TenantAuditMixin, Base):
    """DocumentReference.category (0..*) child table."""

    __tablename__ = "document_reference_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    document_reference = relationship("DocumentReferenceModel", back_populates="categories")
    codings = relationship(
        "DocumentReferenceCategoryCoding",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class DocumentReferenceCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of DocumentReference.category.coding (0..*)."""

    __tablename__ = "document_reference_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_category_id = Column(
        BigInteger,
        ForeignKey("document_reference_category.id"),
        nullable=False,
        index=True,
    )

    category = relationship("DocumentReferenceCategory", back_populates="codings")
