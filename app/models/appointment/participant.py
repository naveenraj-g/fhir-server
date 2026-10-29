from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.appointment.enums import (
    AppointmentParticipantActorReferenceType,
    AppointmentParticipantRequired,
    AppointmentParticipationStatus,
)
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# participant (1..* per spec, modeled as 0..* — see ScheduleActor's
# docstring for the same reasoning) BackboneElement child table
# ---------------------------------------------------------------------------


class AppointmentParticipant(TenantAuditMixin, Base):
    """participant[] — participants involved in the appointment, and their
    role in it.

    `type` (0..* CodeableConcept, see AppointmentParticipantType below) is
    a genuine 3-level nesting from the main resource (Appointment ->
    Participant -> Type -> Coding) — deeper than anything else in this
    codebase so far, but structurally identical to every other
    CodeableConcept-list promotion, just one level further down.

    `actor` (0..1 Reference, polymorphic across 7 possible target types) is
    flattened directly onto this row with the standard
    `{prefix}_reference`/`_type`/`_id`/`_display` + identifier-fallback
    shape — see AppointmentParticipantActorReferenceType's docstring for
    which of the 7 allowed types are actually modeled resources here.

    `required` (0..1) and `status` (1..1, required) are both coded fields;
    `period` (0..1 Period) is flattened to period_start/period_end, same as
    every other Period field in this codebase.
    """

    __tablename__ = "appointment_participant"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )

    # ── actor (0..1 Reference, polymorphic) ───────────────────────────────

    actor_reference = Column(String, nullable=True)
    actor_type = Column(
        Enum(
            AppointmentParticipantActorReferenceType,
            name="appointment_participant_actor_reference_type",
        ),
        nullable=True,
    )
    actor_id = Column(BigInteger, nullable=True, index=True)
    actor_display = Column(String, nullable=True)

    actor_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    actor_identifier_type_system = Column(String, nullable=True)
    actor_identifier_type_version = Column(String, nullable=True)
    actor_identifier_type_code = Column(String, nullable=True)
    actor_identifier_type_display = Column(String, nullable=True)
    actor_identifier_type_text = Column(String, nullable=True)
    actor_identifier_type_user_selected = Column(Boolean, nullable=True)
    actor_identifier_system = Column(String, nullable=True)
    actor_identifier_value = Column(String, nullable=True)
    actor_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    actor_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── required (0..1 code) ──────────────────────────────────────────────

    required = Column(
        Enum(AppointmentParticipantRequired, name="appointment_participant_required"),
        nullable=True,
    )

    # ── status (1..1 code) — required ─────────────────────────────────────

    status = Column(
        Enum(
            AppointmentParticipationStatus, name="appointment_participation_status"
        ),
        nullable=False,
    )

    # ── period (0..1 Period) ──────────────────────────────────────────────

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    appointment = relationship("AppointmentModel", back_populates="participants")
    types = relationship(
        "AppointmentParticipantType",
        back_populates="participant",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# participant.type (0..*) CodeableConcept grandchild table
# ---------------------------------------------------------------------------


class AppointmentParticipantType(TenantAuditMixin, Base):
    """One entry of Appointment.participant.type (0..* CodeableConcept).
    `text` stays flattened (sibling of coding[], not part of it);
    `coding[]` itself is a real 0..* grandgrandchild table
    (AppointmentParticipantTypeCoding, below)."""

    __tablename__ = "appointment_participant_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_participant_id = Column(
        BigInteger, ForeignKey("appointment_participant.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    participant = relationship("AppointmentParticipant", back_populates="types")
    codings = relationship(
        "AppointmentParticipantTypeCoding",
        back_populates="participant_type",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# participant.type.coding (0..*) grandgrandchild table
# ---------------------------------------------------------------------------


class AppointmentParticipantTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Appointment.participant.type.coding (0..*)."""

    __tablename__ = "appointment_participant_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_participant_type_id = Column(
        BigInteger,
        ForeignKey("appointment_participant_type.id"),
        nullable=False,
        index=True,
    )

    participant_type = relationship(
        "AppointmentParticipantType", back_populates="codings"
    )
