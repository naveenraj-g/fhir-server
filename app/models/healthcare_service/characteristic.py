from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# characteristic (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class HealthcareServiceCharacteristic(TenantAuditMixin, Base):
    """characteristic[] — collection of characteristics/features of this
    service. `text` stays flattened (sibling of coding[], not part of it);
    `coding[]` itself is a real 0..* child table
    (HealthcareServiceCharacteristicCoding, below) rather than a single
    flattened coding — same reasoning as OrganizationType's own coding[]
    promotion."""

    __tablename__ = "healthcare_service_characteristic"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="characteristics"
    )
    codings = relationship(
        "HealthcareServiceCharacteristicCoding",
        back_populates="characteristic",
        cascade="all, delete-orphan",
    )


class HealthcareServiceCharacteristicCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of HealthcareService.characteristic.coding (0..*)."""

    __tablename__ = "healthcare_service_characteristic_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_characteristic_id = Column(
        BigInteger,
        ForeignKey("healthcare_service_characteristic.id"),
        nullable=False,
        index=True,
    )

    characteristic = relationship(
        "HealthcareServiceCharacteristic", back_populates="codings"
    )
