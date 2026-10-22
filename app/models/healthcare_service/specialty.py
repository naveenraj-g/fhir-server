from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# specialty (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class HealthcareServiceSpecialty(TenantAuditMixin, Base):
    """specialty[] — medical specialties handled by this service. `text`
    stays flattened (sibling of coding[], not part of it); `coding[]`
    itself is a real 0..* child table (HealthcareServiceSpecialtyCoding,
    below) rather than a single flattened coding — same reasoning as
    OrganizationType's own coding[] promotion."""

    __tablename__ = "healthcare_service_specialty"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="specialties"
    )
    codings = relationship(
        "HealthcareServiceSpecialtyCoding",
        back_populates="specialty",
        cascade="all, delete-orphan",
    )


class HealthcareServiceSpecialtyCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of HealthcareService.specialty.coding (0..*)."""

    __tablename__ = "healthcare_service_specialty_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_specialty_id = Column(
        BigInteger,
        ForeignKey("healthcare_service_specialty.id"),
        nullable=False,
        index=True,
    )

    specialty = relationship("HealthcareServiceSpecialty", back_populates="codings")
