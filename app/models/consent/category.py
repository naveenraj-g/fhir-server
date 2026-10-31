from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ConsentCategory(TenantAuditMixin, Base):
    """Consent.category (1..* CodeableConcept) child table."""

    __tablename__ = "consent_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consent_pk = Column(
        BigInteger, ForeignKey("consent.id", ondelete="CASCADE"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    consent = relationship("ConsentModel", back_populates="categories")
    codings = relationship(
        "ConsentCategoryCoding",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ConsentCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Consent.category[].coding (0..* Coding) grandchild table."""

    __tablename__ = "consent_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_id = Column(
        BigInteger, ForeignKey("consent_category.id", ondelete="CASCADE"), nullable=False, index=True
    )

    category = relationship("ConsentCategory", back_populates="codings")
