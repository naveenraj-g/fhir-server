from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# communication (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class HealthcareServiceCommunication(TenantAuditMixin, Base):
    """communication[] — languages this service is offered in. `text` stays
    flattened (sibling of coding[], not part of it); `coding[]` itself is a
    real 0..* child table (HealthcareServiceCommunicationCoding, below)
    rather than a single flattened coding — same reasoning as
    OrganizationType's own coding[] promotion."""

    __tablename__ = "healthcare_service_communication"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="communications"
    )
    codings = relationship(
        "HealthcareServiceCommunicationCoding",
        back_populates="communication",
        cascade="all, delete-orphan",
    )


class HealthcareServiceCommunicationCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of HealthcareService.communication.coding (0..*)."""

    __tablename__ = "healthcare_service_communication_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_communication_id = Column(
        BigInteger,
        ForeignKey("healthcare_service_communication.id"),
        nullable=False,
        index=True,
    )

    communication = relationship(
        "HealthcareServiceCommunication", back_populates="codings"
    )
