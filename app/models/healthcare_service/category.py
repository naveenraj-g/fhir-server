from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# category (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class HealthcareServiceCategory(TenantAuditMixin, Base):
    """category[] — broad classification of the service being performed.
    `text` stays flattened (sibling of coding[], not part of it); `coding[]`
    itself is a real 0..* child table (HealthcareServiceCategoryCoding,
    below) rather than a single flattened coding — same reasoning as
    OrganizationType's own coding[] promotion."""

    __tablename__ = "healthcare_service_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named healthcare_service_pk, not healthcare_service_id,
    # so it can never be confused with the public sequence ID.
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="categories"
    )
    codings = relationship(
        "HealthcareServiceCategoryCoding",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class HealthcareServiceCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of HealthcareService.category.coding (0..*)."""

    __tablename__ = "healthcare_service_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_category_id = Column(
        BigInteger,
        ForeignKey("healthcare_service_category.id"),
        nullable=False,
        index=True,
    )

    category = relationship("HealthcareServiceCategory", back_populates="codings")
