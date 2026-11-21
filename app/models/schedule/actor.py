from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class ScheduleActor(Base):
    """Search index for the `actor` reference parameter (1..*): one row per
    Schedule.actor that has a `reference` or an `identifier` (one with only
    `display` can't be matched by a reference search). Derived from
    ScheduleModel.content — never read to build a response.

    `actor` can point at seven resource types (Patient | Practitioner |
    PractitionerRole | RelatedPerson | Device | HealthcareService | Location),
    so `reference_type` records which one a relative `Type/<id>` names — a
    search by bare id is ambiguous and R4 requires a type (`actor=Type/id` or
    `actor:Type=id`).

      actor             -> reference_type/reference_id (a relative Type/<id>)
                           or reference_reference (the raw string, for an
                           absolute URL)
      actor:identifier  -> reference_identifier_system/_value

    `reference_type` is a plain string, not a Postgres enum, and there is no
    ForeignKey on `reference_id` (the public id of another resource) and no
    UniqueConstraint: R4 doesn't forbid listing the same actor twice."""

    __tablename__ = "schedule_actor"
    __table_args__ = (
        Index("ix_schedule_actor_type_id", "reference_type", "reference_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_pk = Column(
        BigInteger, ForeignKey("schedule.id"), nullable=False, index=True
    )
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    schedule = relationship("ScheduleModel", back_populates="actors")
