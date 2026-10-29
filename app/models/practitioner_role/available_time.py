from sqlalchemy import BigInteger, Boolean, Column, Enum, ForeignKey, Time
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.practitioner_role.enums import PractitionerRoleDayOfWeek
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

    `days_of_week` is a real Postgres `ARRAY(Enum)` — daysOfWeek carries a
    `required` binding (a closed code list HL7 defines completely), so the
    DB type itself mirrors that enumeration (`practitioner_role_day_of_week`
    Postgres type) rather than leaving it to schema-layer validation alone —
    see `LocationDayOfWeek`'s docstring (`app/models/location/enums.py`) for
    the full reasoning this mirrors.
    """

    __tablename__ = "practitioner_role_available_time"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_pk = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
    )

    days_of_week = Column(
        ARRAY(
            Enum(
                PractitionerRoleDayOfWeek,
                name="practitioner_role_day_of_week",
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
            )
        ),
        nullable=True,
    )
    all_day = Column(Boolean, nullable=True)
    available_start_time = Column(Time, nullable=True)
    available_end_time = Column(Time, nullable=True)

    practitioner_role = relationship(
        "PractitionerRoleModel", back_populates="available_times"
    )
