from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Text, Time
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# availableTime (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class PractitionerRoleAvailableTime(TenantAuditMixin, Base):
    """availableTime[] BackboneElement — times the practitioner is
    available at this location/role.

    BackboneElement fields:
      - daysOfWeek         (0..* code)    mon|tue|wed|thu|fri|sat|sun
      - allDay             (0..1 boolean) true if available all day
      - availableStartTime (0..1 time)    ignored if allDay = true
      - availableEndTime   (0..1 time)    ignored if allDay = true

    `days_of_week` is comma-separated Text per the `daysOfWeek[]` exception in
    /fhir-db-model — same shape as HealthcareServiceAvailableTime. Validated
    against PractitionerRoleDayOfWeek at the schema layer (app.schemas.enums).
    """

    __tablename__ = "practitioner_role_available_time"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_pk = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
    )

    days_of_week = Column(Text, nullable=True)  # comma-separated: mon,tue,…
    all_day = Column(Boolean, nullable=True)
    available_start_time = Column(Time, nullable=True)
    available_end_time = Column(Time, nullable=True)

    practitioner_role = relationship(
        "PractitionerRoleModel", back_populates="available_times"
    )
