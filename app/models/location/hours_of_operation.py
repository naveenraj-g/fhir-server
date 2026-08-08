from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base

# ---------------------------------------------------------------------------
# hoursOfOperation (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class LocationHoursOfOperation(Base):
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
    location_id = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    days_of_week = Column(Text, nullable=True)  # comma-separated: mon,tue,…
    all_day = Column(Boolean, nullable=True)
    opening_time = Column(Time, nullable=True)
    closing_time = Column(Time, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    location = relationship("LocationModel", back_populates="hours_of_operation")
