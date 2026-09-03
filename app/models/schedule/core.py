from sqlalchemy import BigInteger, Boolean, Column, DateTime, Sequence, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base

schedule_id_seq = Sequence(
    "schedule_pub_seq", start=200000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class ScheduleModel(Base):
    """FHIR R4 Schedule — https://www.hl7.org/fhir/R4/schedule.html

    A container for slots of time that may be available for booking
    appointments.

    Modeled to the same conventions as Organization/Location/HealthcareService/
    PractitionerRole: BigInteger internal PK + public sequence ID, full
    six-column CodeableConcept flattening, and a flattened polymorphic
    reference for `actor` (`actor_type`/`actor_id`/`actor_display`, storing
    the target's PUBLIC sequence ID with no ForeignKey/relationship — see
    CLAUDE.md's FHIR DB Model Design section) with an Identifier
    logical-reference fallback where the target may live outside this system.

    Part of the Patient/Practitioner/Organization/Location/HealthcareService/
    PractitionerRole JWT auth rollout: org_id comes from the verified JWT's
    activeOrganizationId claim (actor.org_id), never a client-suppliable
    field. There is deliberately no user_id: like Organization, Location,
    HealthcareService, and PractitionerRole, a Schedule is a shared org-level
    scheduling artifact for an actor, not something scoped to one end user.
    """

    __tablename__ = "schedule"

    # Internal PK — never exposed. BigInteger so every child table's FK shares
    # the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    schedule_id = Column(
        BigInteger,
        schedule_id_seq,
        server_default=schedule_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    org_id = Column(String, nullable=False, index=True)

    # ── active (0..1 boolean) ────────────────────────────────────────────────

    active = Column(Boolean, nullable=False, default=False)

    # ── planningHorizon (0..1 Period) — flattened ───────────────────────────

    planning_horizon_start = Column(DateTime(timezone=True), nullable=True)
    planning_horizon_end = Column(DateTime(timezone=True), nullable=True)

    # ── comment (0..1 string) ───────────────────────────────────────────────

    comment = Column(Text, nullable=True)

    # ── Audit ────────────────────────────────────────────────────────────────

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────

    identifiers = relationship(
        "ScheduleIdentifier",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
    service_categories = relationship(
        "ScheduleServiceCategory",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
    service_types = relationship(
        "ScheduleServiceType",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
    specialties = relationship(
        "ScheduleSpecialty",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
    actors = relationship(
        "ScheduleActor",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
