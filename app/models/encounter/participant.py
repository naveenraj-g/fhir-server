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
from app.models.encounter.enums import EncounterParticipantIndividualReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# participant (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class EncounterParticipant(TenantAuditMixin, Base):
    """participant[] — the list of people responsible for providing the
    service.

    `type` (0..* CodeableConcept, see EncounterParticipantType below) is
    a 3-level-deep nesting from the main resource (Encounter ->
    Participant -> Type -> Coding) — same shape and same eager-load
    requirement as Appointment.participant.type (see CLAUDE.md's
    "A CodeableConcept-list field living inside a 0..* BackboneElement
    nests 3 levels deep" invariant).

    `individual` (0..1 Reference, polymorphic across 3 possible target
    types) is flattened directly onto this row — see
    EncounterParticipantIndividualReferenceType's docstring for which of
    the 3 allowed types are actually modeled resources here.

    Unlike Appointment.participant, Encounter.participant has no
    `required`/`status` fields — just `type`, `period`, `individual`.
    """

    __tablename__ = "encounter_participant"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # ── individual (0..1 Reference, polymorphic) ──────────────────────────

    individual_reference = Column(String, nullable=True)
    individual_type = Column(
        Enum(
            EncounterParticipantIndividualReferenceType,
            name="encounter_participant_individual_reference_type",
        ),
        nullable=True,
    )
    individual_id = Column(BigInteger, nullable=True, index=True)
    individual_display = Column(String, nullable=True)

    individual_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    individual_identifier_type_system = Column(String, nullable=True)
    individual_identifier_type_version = Column(String, nullable=True)
    individual_identifier_type_code = Column(String, nullable=True)
    individual_identifier_type_display = Column(String, nullable=True)
    individual_identifier_type_text = Column(String, nullable=True)
    individual_identifier_type_user_selected = Column(Boolean, nullable=True)
    individual_identifier_system = Column(String, nullable=True)
    individual_identifier_value = Column(String, nullable=True)
    individual_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    individual_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="participants")
    types = relationship(
        "EncounterParticipantType", back_populates="participant", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# participant.type (0..*) CodeableConcept grandchild table
# ---------------------------------------------------------------------------


class EncounterParticipantType(TenantAuditMixin, Base):
    """One entry of Encounter.participant.type (0..* CodeableConcept).
    `text` stays flattened; `coding[]` is a real 0..* grandgrandchild
    table (EncounterParticipantTypeCoding, below)."""

    __tablename__ = "encounter_participant_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_participant_id = Column(
        BigInteger, ForeignKey("encounter_participant.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    participant = relationship("EncounterParticipant", back_populates="types")
    codings = relationship(
        "EncounterParticipantTypeCoding", back_populates="participant_type", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# participant.type.coding (0..*) grandgrandchild table
# ---------------------------------------------------------------------------


class EncounterParticipantTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Encounter.participant.type.coding (0..*)."""

    __tablename__ = "encounter_participant_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_participant_type_id = Column(
        BigInteger, ForeignKey("encounter_participant_type.id"), nullable=False, index=True
    )

    participant_type = relationship("EncounterParticipantType", back_populates="codings")
