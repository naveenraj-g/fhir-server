from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# program (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class HealthcareServiceProgram(TenantAuditMixin, Base):
    """program[] — government or local programs this service applies to.
    `text` stays flattened (sibling of coding[], not part of it); `coding[]`
    itself is a real 0..* child table (HealthcareServiceProgramCoding,
    below) rather than a single flattened coding — same reasoning as
    OrganizationType's own coding[] promotion."""

    __tablename__ = "healthcare_service_program"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="programs"
    )
    codings = relationship(
        "HealthcareServiceProgramCoding",
        back_populates="program",
        cascade="all, delete-orphan",
    )


class HealthcareServiceProgramCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of HealthcareService.program.coding (0..*)."""

    __tablename__ = "healthcare_service_program_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_program_id = Column(
        BigInteger,
        ForeignKey("healthcare_service_program.id"),
        nullable=False,
        index=True,
    )

    program = relationship("HealthcareServiceProgram", back_populates="codings")
