from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.schedule.enums import ScheduleActorReferenceType

# ---------------------------------------------------------------------------
# actor (1..*) polymorphic Reference child table
# ---------------------------------------------------------------------------


class ScheduleActor(Base):
    """actor[] — resource(s) that availability information is being provided
    for: Patient | Practitioner | PractitionerRole | RelatedPerson | Device |
    HealthcareService | Location (a single shared `reference_type` enum
    covers all seven, dispatched dynamically at existence-check time by
    `app.core.reference_resolver.ensure_resource_exists()` — no special
    handling needed for the polymorphism beyond registering each type in
    RESOURCE_REGISTRY). No Device model exists in this codebase, so a Device
    actor reference gets no existence check — same treatment as
    HealthcareServiceEndpoint's unmodeled Endpoint target; the identifier
    fallback is the only populated half for that case.

    reference_id stores the target's PUBLIC sequence ID — no FK/relationship,
    same flattened-reference convention as every other reworked resource.
    """

    __tablename__ = "schedule_actor"
    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            "reference_type",
            "reference_id",
            name="uq_schedule_actor_reference",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_id = Column(
        BigInteger, ForeignKey("schedule.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    reference_type = Column(
        Enum(ScheduleActorReferenceType, name="schedule_actor_reference_type"),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # actor.identifier (0..1 Identifier) — logical-reference fallback for an
    # actor held in another system (or a Device, which isn't modeled here)
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    schedule = relationship("ScheduleModel", back_populates="actors")
