from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# appointmentType.coding (0..*) child table
# ---------------------------------------------------------------------------


class AppointmentAppointmentTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Appointment.appointmentType.coding (0..*).

    appointmentType itself is a 0..1 CodeableConcept living directly on the
    main `appointment` row — its `text` sibling field is flattened onto
    AppointmentModel (`appointment_type_text`), but `coding[]` still gets
    this dedicated child table, FK'd straight to `appointment.id` — same
    reasoning as SlotAppointmentTypeCoding's promotion.
    """

    __tablename__ = "appointment_appointment_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )

    appointment = relationship(
        "AppointmentModel", back_populates="appointment_type_codings"
    )
