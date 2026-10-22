from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# serviceProvisionCode (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class HealthcareServiceServiceProvisionCode(TenantAuditMixin, Base):
    """serviceProvisionCode[] — conditions under which service is
    available/offered. `text` stays flattened (sibling of coding[], not
    part of it); `coding[]` itself is a real 0..* child table
    (HealthcareServiceServiceProvisionCodeCoding, below) rather than a
    single flattened coding — same reasoning as OrganizationType's own
    coding[] promotion."""

    __tablename__ = "healthcare_service_service_provision_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="service_provision_codes"
    )
    codings = relationship(
        "HealthcareServiceServiceProvisionCodeCoding",
        back_populates="service_provision_code",
        cascade="all, delete-orphan",
    )


class HealthcareServiceServiceProvisionCodeCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """One entry of HealthcareService.serviceProvisionCode.coding (0..*)."""

    __tablename__ = "healthcare_service_service_provision_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_service_provision_code_id = Column(
        BigInteger,
        ForeignKey("healthcare_service_service_provision_code.id"),
        nullable=False,
        index=True,
    )

    service_provision_code = relationship(
        "HealthcareServiceServiceProvisionCode", back_populates="codings"
    )
