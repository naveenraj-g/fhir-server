from sqlalchemy import BigInteger, Boolean, Column, Enum, ForeignKey, Time
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.healthcare_service.enums import HealthcareServiceDayOfWeek
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

    `days_of_week` is a real Postgres `ARRAY(Enum)` — daysOfWeek carries a
    `required` binding (a closed code list HL7 defines completely), so the
    DB type itself mirrors that enumeration (`healthcare_service_day_of_week`
    Postgres type) rather than leaving it to schema-layer validation alone —
    see `LocationDayOfWeek`'s docstring (`app/models/location/enums.py`) for
    the full reasoning this mirrors.

    start/end use SQL `TIME`, not String: FHIR `time` is a wall-clock time
    with no date and no timezone, which is exactly what TIME stores — same
    choice as LocationHoursOfOperation.opening_time/closing_time.
    """

    __tablename__ = "healthcare_service_available_time"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )

    days_of_week = Column(
        ARRAY(
            Enum(
                HealthcareServiceDayOfWeek,
                name="healthcare_service_day_of_week",
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
            )
        ),
        nullable=True,
    )
    all_day = Column(Boolean, nullable=True)
    available_start_time = Column(Time, nullable=True)
    available_end_time = Column(Time, nullable=True)

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="available_times"
    )
