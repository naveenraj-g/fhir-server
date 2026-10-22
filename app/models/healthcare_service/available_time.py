from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Text, Time
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# availableTime (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class HealthcareServiceAvailableTime(TenantAuditMixin, Base):
    """availableTime[] BackboneElement — times the service site is available.

    BackboneElement fields:
      - daysOfWeek         (0..* code)    mon|tue|wed|thu|fri|sat|sun
      - allDay             (0..1 boolean) true if available all day
      - availableStartTime (0..1 time)    ignored if allDay = true
      - availableEndTime   (0..1 time)    ignored if allDay = true

    `days_of_week` is comma-separated Text per the `daysOfWeek[]` exception in
    /fhir-db-model — the values are never filtered individually, so a child
    table would add a join for nothing. Validated against
    HealthcareServiceDayOfWeek at the schema layer.

    start/end use SQL `TIME`, not String: FHIR `time` is a wall-clock time
    with no date and no timezone, which is exactly what TIME stores — same
    choice as LocationHoursOfOperation.opening_time/closing_time.
    """

    __tablename__ = "healthcare_service_available_time"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )

    days_of_week = Column(Text, nullable=True)  # comma-separated: mon,tue,…
    all_day = Column(Boolean, nullable=True)
    available_start_time = Column(Time, nullable=True)
    available_end_time = Column(Time, nullable=True)

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="available_times"
    )
