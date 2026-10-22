from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# type (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class HealthcareServiceType(TenantAuditMixin, Base):
    """type[] — specific type of service within the category. `text` stays
    flattened (sibling of coding[], not part of it); `coding[]` itself is a
    real 0..* child table (HealthcareServiceTypeCoding, below) rather than
    a single flattened coding — same reasoning as OrganizationType's own
    coding[] promotion."""

    __tablename__ = "healthcare_service_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    healthcare_service = relationship("HealthcareServiceModel", back_populates="types")
    codings = relationship(
        "HealthcareServiceTypeCoding",
        back_populates="type",
        cascade="all, delete-orphan",
    )


class HealthcareServiceTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of HealthcareService.type.coding (0..*)."""

    __tablename__ = "healthcare_service_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_type_id = Column(
        BigInteger, ForeignKey("healthcare_service_type.id"), nullable=False, index=True
    )

    type = relationship("HealthcareServiceType", back_populates="codings")
