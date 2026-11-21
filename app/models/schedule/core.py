from sqlalchemy import BigInteger, Boolean, Column, DateTime, Index, Sequence
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

schedule_id_seq = Sequence(
    "schedule_pub_seq", start=200000, increment=1, metadata=Base.metadata
)


class ScheduleModel(TenantAuditMixin, Base):
    """FHIR R4 Schedule — Medplum-style storage, same as Organization,
    Location, Practitioner, HealthcareService, Endpoint and PractitionerRole.

    `content` (JSONB) holds the whole resource exactly as validated on
    write; it is the single source of truth, and GET serves it back as-is
    (`id`/`meta` are stamped on at read time from this row's own columns —
    see app.fhir.mappers.schedule). Nothing else in this table or its child
    tables is a second copy of the resource: every other column exists only
    because a FHIR R4 Schedule search parameter filters on it
    (https://www.hl7.org/fhir/R4/schedule.html#search), and is derived from
    `content` on every write by app.repository.schedule._indexer.

    Search parameter -> storage:
      active            -> active (0..1, column)
      date              -> planning_horizon_start / planning_horizon_end
                           (0..1 Period, two columns; matched as a range — see
                           app.fhir.search.sql.period_match)
      identifier        -> ScheduleIdentifier (0..*)
      service-category,
      service-type,
      specialty         -> ScheduleToken (0..*, one row per coding, `param`
                           says which search parameter it feeds)
      actor             -> ScheduleActor (1..*, a Reference to one of seven
                           resource types — `reference_type` says which)
      _id               -> schedule_id;  _lastUpdated -> updated_at/created_at

    `comment` and `extension` have no search parameter and live only in
    `content`.

    `planning_horizon_start` is the first instant the period covers and
    `planning_horizon_end` the first instant *after* it (see
    app.repository._content_index.period_bounds), NULL meaning open.

    No `user_id`: a Schedule is a shared tenant-level entity. No DB-level
    CHECK constraints — every R4 rule (e.g. `actor` is 1..*) is enforced by the
    FHIR validator before anything is written."""

    __tablename__ = "schedule"
    __table_args__ = (
        Index(
            "ix_schedule_planning_horizon",
            "planning_horizon_start",
            "planning_horizon_end",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    schedule_id = Column(
        BigInteger,
        schedule_id_seq,
        server_default=schedule_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    active = Column(Boolean, nullable=True)
    planning_horizon_start = Column(DateTime(timezone=True), nullable=True)
    planning_horizon_end = Column(DateTime(timezone=True), nullable=True)

    identifiers = relationship(
        "ScheduleIdentifier", back_populates="schedule", cascade="all, delete-orphan"
    )
    tokens = relationship(
        "ScheduleToken", back_populates="schedule", cascade="all, delete-orphan"
    )
    actors = relationship(
        "ScheduleActor", back_populates="schedule", cascade="all, delete-orphan"
    )
