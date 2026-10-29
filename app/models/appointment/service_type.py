from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# serviceType (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class AppointmentServiceType(TenantAuditMixin, Base):
    """serviceType[] — the specific service that is to be performed during
    this appointment. `text` stays flattened (sibling of coding[], not part
    of it); `coding[]` itself is a real 0..* child table
    (AppointmentServiceTypeCoding, below) — same reasoning as
    SlotServiceType's own coding[] promotion."""

    __tablename__ = "appointment_service_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="service_types")
    codings = relationship(
        "AppointmentServiceTypeCoding",
        back_populates="service_type",
        cascade="all, delete-orphan",
    )


class AppointmentServiceTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Appointment.serviceType.coding (0..*)."""

    __tablename__ = "appointment_service_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_service_type_id = Column(
        BigInteger, ForeignKey("appointment_service_type.id"), nullable=False, index=True
    )

    service_type = relationship("AppointmentServiceType", back_populates="codings")
