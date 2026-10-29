from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# specialty (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class AppointmentSpecialty(TenantAuditMixin, Base):
    """specialty[] — the specialty of a practitioner that would be required
    to perform the service requested in this appointment. `text` stays
    flattened (sibling of coding[], not part of it); `coding[]` itself is a
    real 0..* child table (AppointmentSpecialtyCoding, below) — same
    reasoning as SlotSpecialty's own coding[] promotion."""

    __tablename__ = "appointment_specialty"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="specialties")
    codings = relationship(
        "AppointmentSpecialtyCoding",
        back_populates="specialty",
        cascade="all, delete-orphan",
    )


class AppointmentSpecialtyCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Appointment.specialty.coding (0..*)."""

    __tablename__ = "appointment_specialty_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_specialty_id = Column(
        BigInteger, ForeignKey("appointment_specialty.id"), nullable=False, index=True
    )

    specialty = relationship("AppointmentSpecialty", back_populates="codings")
