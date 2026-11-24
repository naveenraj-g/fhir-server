from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import GoalLifecycleStatus

goal_id_seq = Sequence(
    "goal_pub_seq", start=460000, increment=1, metadata=Base.metadata
)

# The R4 targets of Goal.subject.
SUBJECT_TYPES = ("Patient", "Group", "Organization")


class GoalModel(TenantAuditMixin, Base):
    """FHIR R4 Goal - content-based storage, same as CarePlan, CareTeam, Patient and the other
    rebuilt resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.goal). Every other column exists only because a
    FHIR R4 Goal search parameter filters on it (https://www.hl7.org/fhir/R4/goal.html#search)
    and is derived from `content` on every write by app.repository.goal._indexer.

    Search parameter -> storage:
      lifecycle-status   -> lifecycle_status (1..1 code, Enum column, stored by value so `on-hold`
                            / `entered-in-error` are the real FHIR codes)
      start-date         -> start_start/_end (`startDate`, the half-open range the date covers;
                            a `startCodeableConcept` is not a date, so it is not indexed; columns)
      subject, patient   -> subject_reference/_type/_id + subject_identifier_* (1..1
                            Reference(Patient | Group | Organization), columns; `patient` is
                            `subject` narrowed to Patients)
      identifier         -> GoalIdentifier (0..*)
      achievement-status, category
                         -> GoalToken (one shared table, one row per coding of each concept,
                            told apart by `param`)
      target-date        -> GoalTarget (one row per target with a `dueDate`)
      _id                -> goal_id;  _lastUpdated -> updated_at/created_at

    Everything else (`priority`, `description`, `start[x]` as a CodeableConcept, `target` apart
    from its due date, `statusDate`, `statusReason`, `expressedBy`, `addresses`, `note`,
    `outcomeCode`, `outcomeReference`, `extension`) has no search parameter and lives only in
    `content`.

    `subject` points at three resource types, so a search by bare id is ambiguous
    (`subject=Type/id` or `subject:Type=id`); `patient` is `subject` narrowed to Patients (a
    Group, an Organization or a logical subject counts as missing it).

    All index columns are nullable. No `user_id`: a Goal is a shared tenant-level entity. No
    DB-level CHECK constraints."""

    __tablename__ = "goal"
    __table_args__ = (
        Index("ix_goal_start", "start_start", "start_end"),
        Index("ix_goal_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    goal_id = Column(
        BigInteger,
        goal_id_seq,
        server_default=goal_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    lifecycle_status = Column(
        Enum(
            GoalLifecycleStatus,
            name="goal_lifecycle_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # startDate: the half-open [start, end) range of instants the date covers (NULL = absent).
    start_start = Column(DateTime(timezone=True), nullable=True)
    start_end = Column(DateTime(timezone=True), nullable=True)

    # subject (1..1 Reference(Patient | Group | Organization))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(String, nullable=True)
    subject_id = Column(BigInteger, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "GoalIdentifier", back_populates="goal", cascade="all, delete-orphan"
    )
    tokens = relationship(
        "GoalToken", back_populates="goal", cascade="all, delete-orphan"
    )
    targets = relationship(
        "GoalTarget", back_populates="goal", cascade="all, delete-orphan"
    )
