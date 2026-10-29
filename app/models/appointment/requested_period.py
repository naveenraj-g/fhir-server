from sqlalchemy import BigInteger, Column, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# requestedPeriod (0..*) Period child table
# ---------------------------------------------------------------------------


class AppointmentRequestedPeriod(TenantAuditMixin, Base):
    """requestedPeriod[] — potential date/time interval(s) requested to
    allocate the appointment within. A Period has no coding/text to
    promote — just start/end — so this is a flat child table with no
    grandchild."""

    __tablename__ = "appointment_requested_period"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )
    start = Column(DateTime(timezone=True), nullable=True)
    end = Column(DateTime(timezone=True), nullable=True)

    appointment = relationship("AppointmentModel", back_populates="requested_periods")
