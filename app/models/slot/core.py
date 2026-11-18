from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import ScheduleReferenceType
from app.models.shared import TenantAuditMixin

from .enums import SlotStatus

slot_id_seq = Sequence("slot_pub_seq", start=220000, increment=1, metadata=Base.metadata)


class SlotModel(TenantAuditMixin, Base):
    """FHIR R4 Slot — Medplum-style storage, same as Organization, Location,
    Practitioner, HealthcareService, Endpoint, PractitionerRole and Schedule.

    `content` (JSONB) holds the whole resource exactly as validated on
    write; it is the single source of truth, and GET serves it back as-is
    (`id`/`meta` are stamped on at read time from this row's own columns —
    see app.fhir.mappers.slot). Nothing else in this table or its child
    tables is a second copy of the resource: every other column exists only
    because a FHIR R4 Slot search parameter filters on it
    (https://www.hl7.org/fhir/R4/slot.html#search), and is derived from
    `content` on every write by app.repository.slot._indexer.

    Search parameter -> storage:
      status            -> status (1..1 code, Enum column, stored by value)
      start             -> start (1..1 instant, column)
      schedule          -> schedule_reference/_type/_id +
                           schedule_identifier_system/_value (1..1, columns)
      identifier        -> SlotIdentifier (0..*)
      service-category,
      service-type,
      specialty,
      appointment-type  -> SlotToken (one row per coding, `param` says which
                           search parameter it feeds)
      _id               -> slot_id;  _lastUpdated -> updated_at/created_at

    `end`, `overbooked`, `comment` and `extension` have no search parameter and
    live only in `content` (so a range query on a slot's end isn't indexed —
    R4 has no `end` search parameter).

    All index columns are nullable: R4 makes `schedule`, `status`, `start` and
    `end` mandatory, but that is the validator's rule (enforced by the
    `java_validator` backend), not the database's. No `user_id`: a Slot is a
    shared tenant-level entity. No DB-level CHECK constraints."""

    __tablename__ = "slot"
    __table_args__ = (Index("ix_slot_schedule_start", "schedule_id", "start"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    slot_id = Column(
        BigInteger,
        slot_id_seq,
        server_default=slot_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    status = Column(
        Enum(
            SlotStatus,
            name="slot_status",
            # Store `busy-unavailable`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    start = Column(DateTime(timezone=True), nullable=True, index=True)
    # schedule (1..1 Reference(Schedule)). `schedule_reference` is the raw
    # literal string exactly as received (kept whether or not it resolves
    # locally); `schedule_type`/`schedule_id` are the resolved type and PUBLIC
    # id for a relative Schedule/<id> (no FK — see CLAUDE.md's
    # flattened-reference convention); `schedule_identifier_*` is
    # Reference.identifier, for `schedule:identifier`.
    schedule_reference = Column(String, nullable=True)
    schedule_type = Column(
        Enum(ScheduleReferenceType, name="schedule_reference_type", create_type=False),
        nullable=True,
    )
    schedule_id = Column(BigInteger, nullable=True)
    schedule_identifier_system = Column(String, nullable=True)
    schedule_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "SlotIdentifier", back_populates="slot", cascade="all, delete-orphan"
    )
    tokens = relationship("SlotToken", back_populates="slot", cascade="all, delete-orphan")
