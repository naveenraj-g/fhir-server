from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import ARRAY
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

    `days_of_week` is a real Postgres `ARRAY(String)`, same as
    `HealthcareServiceAvailableTime.days_of_week`/`Address.line`/
    `HumanName.given`/`prefix`/`suffix` — the former comma-separated-Text
    "exception" documented in /fhir-db-model conflated "don't promote this to
    a child table" (still correct — there's nothing to join on) with "don't
    use a plain array column either" (not actually justified; an array is
    one column, not a join). Validated against PractitionerRoleDayOfWeek at
    the schema layer (app.schemas.enums).
    """

    __tablename__ = "practitioner_role_available_time"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_pk = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
    )

    days_of_week = Column(ARRAY(String), nullable=True)
    all_day = Column(Boolean, nullable=True)
    available_start_time = Column(Time, nullable=True)
    available_end_time = Column(Time, nullable=True)

    practitioner_role = relationship(
        "PractitionerRoleModel", back_populates="available_times"
    )
