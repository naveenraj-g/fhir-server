from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.slot.enums import SlotScheduleReferenceType, SlotStatus

slot_id_seq = Sequence(
    "slot_pub_seq", start=220000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class SlotModel(Base):
    """FHIR R4 Slot — https://www.hl7.org/fhir/R4/slot.html

    A slot of time on a Schedule that may be available for booking
    appointments.

    Modeled to the same conventions as Schedule (the resource it always
    references 1..1): BigInteger internal PK + public sequence ID, full
    six-column CodeableConcept flattening for serviceCategory/serviceType/
    specialty/appointmentType, and a flattened `schedule` Reference
    (`schedule_type`/`schedule_id`/`schedule_display`, storing Schedule's
    PUBLIC sequence ID with no ForeignKey/relationship — see CLAUDE.md's FHIR
    DB Model Design section) rather than the legacy `schedule_fk_id`
    ForeignKey(schedule.id) this table used before Schedule itself was
    reworked onto the flattened-reference convention.

    Part of the Patient/Practitioner/Organization/Location/HealthcareService/
    PractitionerRole/Schedule JWT auth rollout: org_id comes from the
    verified JWT's activeOrganizationId claim (actor.org_id), never a
    client-suppliable field. There is deliberately no user_id: like Schedule,
    a Slot is a shared org-level scheduling artifact, not something scoped to
    one end user.
    """

    __tablename__ = "slot"

    # Internal PK — never exposed. BigInteger so every child table's FK shares
    # the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    slot_id = Column(
        BigInteger,
        slot_id_seq,
        server_default=slot_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    org_id = Column(String, nullable=False, index=True)

    # ── schedule (1..1 Reference(Schedule)) — flattened, no FK ──────────────

    schedule_type = Column(
        Enum(SlotScheduleReferenceType, name="slot_schedule_reference_type"),
        nullable=False,
    )
    schedule_id = Column(BigInteger, nullable=False, index=True)
    schedule_display = Column(String, nullable=True)

    # schedule.identifier (0..1 Identifier) — logical-reference fallback for
    # the rare case where the schedule isn't a resource in this system
    schedule_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    schedule_identifier_type_system = Column(String, nullable=True)
    schedule_identifier_type_version = Column(String, nullable=True)
    schedule_identifier_type_code = Column(String, nullable=True)
    schedule_identifier_type_display = Column(String, nullable=True)
    schedule_identifier_type_text = Column(String, nullable=True)
    schedule_identifier_type_user_selected = Column(Boolean, nullable=True)
    schedule_identifier_system = Column(String, nullable=True)
    schedule_identifier_value = Column(String, nullable=True)
    schedule_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    schedule_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── status (1..1 code) ───────────────────────────────────────────────────

    status = Column(Enum(SlotStatus, name="slot_status"), nullable=False)

    # ── start / end (1..1 instant) ──────────────────────────────────────────

    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True), nullable=False)

    # ── appointmentType (0..1 CodeableConcept) ──────────────────────────────

    appointment_type_system = Column(String, nullable=True)
    appointment_type_version = Column(String, nullable=True)
    appointment_type_code = Column(String, nullable=True)
    appointment_type_display = Column(String, nullable=True)
    appointment_type_text = Column(String, nullable=True)
    appointment_type_user_selected = Column(Boolean, nullable=True)

    # ── overbooked (0..1 boolean) ────────────────────────────────────────────

    overbooked = Column(Boolean, nullable=True)

    # ── comment (0..1 string) ───────────────────────────────────────────────

    comment = Column(Text, nullable=True)

    # ── Audit ────────────────────────────────────────────────────────────────

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────

    identifiers = relationship(
        "SlotIdentifier", back_populates="slot", cascade="all, delete-orphan"
    )
    service_categories = relationship(
        "SlotServiceCategory", back_populates="slot", cascade="all, delete-orphan"
    )
    service_types = relationship(
        "SlotServiceType", back_populates="slot", cascade="all, delete-orphan"
    )
    specialties = relationship(
        "SlotSpecialty", back_populates="slot", cascade="all, delete-orphan"
    )
