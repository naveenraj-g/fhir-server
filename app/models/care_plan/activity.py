from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The nine R4 targets of CarePlan.activity.reference.
ACTIVITY_REFERENCE_TYPES = (
    "Appointment",
    "CommunicationRequest",
    "DeviceRequest",
    "MedicationRequest",
    "NutritionOrder",
    "Task",
    "ServiceRequest",
    "VisionPrescription",
    "RequestGroup",
)


class CarePlanActivity(Base):
    """Search index for the two activity parameters `activity-reference` (CarePlan.activity.reference)
    and `activity-date` (CarePlan.activity.detail.scheduled[x]): one row per activity that has a
    reference or a schedule. Derived from CarePlanModel.content - never read to build a response.

    `reference_type` records which type a relative `Type/<id>` names - a plain string, not a
    Postgres enum, because the reference can be one of nine types (a search by bare id is
    ambiguous: `activity-reference=Type/id` or `:Type=id`). `scheduled_start`/`_end` are the
    half-open range of instants the schedule covers: a Period from its start to the instant after
    its end, a Timing from its earliest event to the instant after its latest (else its
    `repeat.boundsPeriod`); NULL = open. A `scheduledString` is not a date and is not indexed.

      activity-reference             -> reference_type/reference_id or reference_reference
      activity-reference:identifier  -> reference_identifier_system/_value
      activity-date                  -> scheduled_start/_end

    Everything else under `activity` lives only in `content`."""

    __tablename__ = "care_plan_activity"
    __table_args__ = (
        Index("ix_care_plan_activity_type_id", "reference_type", "reference_id"),
        Index("ix_care_plan_activity_scheduled", "scheduled_start", "scheduled_end"),
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
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="activities")
