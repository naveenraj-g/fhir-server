from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The eight R4 targets of CarePlan.activity.detail.performer.
PERFORMER_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "CareTeam",
    "HealthcareService",
    "Patient",
    "Device",
    "RelatedPerson",
)


class CarePlanPerformer(Base):
    """Search index for `performer` (CarePlan.activity.detail.performer of *every* activity, 0..* References): one row per performer with a
    `reference` or an `identifier`. Derived from CarePlanModel.content — never
    read to build a response.

    `reference_type` records which type a relative `Type/<id>` names — a plain
    string, not a Postgres enum, because a performer can be one of eight types (a
    search by bare id is ambiguous: `performer=Type/id` or `:Type=id`).

      performer             -> reference_type/reference_id or reference_reference
      performer:identifier  -> reference_identifier_system/_value
    """

    __tablename__ = "care_plan_performer"
    __table_args__ = (
        Index("ix_care_plan_performer_type_id", "reference_type", "reference_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="performers")
