from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# serviceCategory (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class AppointmentServiceCategory(TenantAuditMixin, Base):
    """serviceCategory[] — a broad categorization of the service for this
    appointment. `text` stays flattened (sibling of coding[], not part of
    it); `coding[]` itself is a real 0..* child table
    (AppointmentServiceCategoryCoding, below) rather than a single
    flattened coding — same reasoning as SlotServiceCategory's own coding[]
    promotion."""

    __tablename__ = "appointment_service_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="service_categories")
    codings = relationship(
        "AppointmentServiceCategoryCoding",
        back_populates="service_category",
        cascade="all, delete-orphan",
    )


class AppointmentServiceCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Appointment.serviceCategory.coding (0..*)."""

    __tablename__ = "appointment_service_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_service_category_id = Column(
        BigInteger,
        ForeignKey("appointment_service_category.id"),
        nullable=False,
        index=True,
    )

    service_category = relationship(
        "AppointmentServiceCategory", back_populates="codings"
    )
