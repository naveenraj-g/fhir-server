from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Text,
    Time,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# hoursOfOperation (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class LocationHoursOfOperation(TenantAuditMixin, Base):
    """Location.hoursOfOperation[] — what days/times the location is usually
    open.

    BackboneElement fields:
      - daysOfWeek  (0..* code)     mon|tue|wed|thu|fri|sat|sun
      - allDay      (0..1 boolean)  true if open 24 hours
      - openingTime (0..1 time)
      - closingTime (0..1 time)

    `days_of_week` is comma-separated Text per the `daysOfWeek[]` exception in
    /fhir-db-model — the values are never filtered individually, so a child
    table would add a join for nothing. Validated against LocationDayOfWeek at
    the schema layer.

    opening/closing use SQL `TIME`, not String: FHIR `time` is a wall-clock
    time with no date and no timezone, which is exactly what TIME stores, and
    it keeps "open before 09:00" answerable in SQL.
    """

    __tablename__ = "location_hours_of_operation"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named location_pk, not location_id, so it can never
    # be confused with LocationModel.location_id (the public, FHIR-facing
    # sequence ID) — same reasoning as Organization's organization_pk.
    location_pk = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )

    days_of_week = Column(Text, nullable=True)  # comma-separated: mon,tue,…
    all_day = Column(Boolean, nullable=True)
    opening_time = Column(Time, nullable=True)
    closing_time = Column(Time, nullable=True)

    location = relationship("LocationModel", back_populates="hours_of_operation")
