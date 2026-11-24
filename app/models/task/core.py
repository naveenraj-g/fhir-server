from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.resource_types import ANY_RESOURCE_TYPES

from .enums import TaskIntent, TaskPriority, TaskStatus

task_id_seq = Sequence(
    "task_pub_seq", start=280000, increment=1, metadata=Base.metadata
)

# The R4 targets of the 0..1 reference elements held as columns. `for` and `focus` are
# Reference(Any): R4 allows every resource type, so the whole R4 list is the target (the shared
# tuple: `is_any()` checks identity).
FOR_TYPES = ANY_RESOURCE_TYPES
FOCUS_TYPES = ANY_RESOURCE_TYPES
ENCOUNTER_TYPES = ("Encounter",)
REQUESTER_TYPES = (
    "Device",
    "Organization",
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
)
OWNER_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "CareTeam",
    "HealthcareService",
    "Patient",
    "Device",
    "RelatedPerson",
)


def _enum(cls, name):
    # Stored by value, so `in-progress` / `original-order` are the real FHIR codes.
    return Enum(
        cls, name=name, values_callable=lambda enum_cls: [m.value for m in enum_cls]
    )


class TaskModel(TenantAuditMixin, Base):
    """FHIR R4 Task - content-based storage, same as Goal, CarePlan, Patient and the other rebuilt
    resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.task). Every other column exists only because a
    FHIR R4 Task search parameter filters on it (https://www.hl7.org/fhir/R4/task.html#search)
    and is derived from `content` on every write by app.repository.task._indexer.

    Search parameter -> storage:
      status, intent, priority
                         -> status / intent / priority (Enum columns, stored by value so
                            `in-progress` / `original-order` are the real FHIR codes)
      authored-on, modified, period
                         -> authored_start/_end (`authoredOn`), modified_start/_end
                            (`lastModified`) and period_start/_end (`executionPeriod`): the
                            half-open range each covers (NULL = absent / open); columns
      group-identifier   -> group_identifier_system/_value (the 0..1 `groupIdentifier`, columns)
      subject, patient   -> for_reference/_type/_id + for_identifier_* (0..1 Reference(Any);
                            `patient` is `subject` narrowed to Patients)
      focus              -> focus_reference/_type/_id + focus_identifier_* (0..1 Reference(Any))
      encounter          -> encounter_reference/_type/_id + encounter_identifier_*
      requester, owner   -> requester_* / owner_* (0..1 multi-target references, columns)
      identifier         -> TaskIdentifier (0..*)
      business-status, code, performer
                         -> TaskToken (one shared table, one row per coding of each concept,
                            told apart by `param`; `performer` reads `performerType`)
      based-on, part-of  -> TaskReference (one shared table, told apart by `param`)
      _id                -> task_id;  _lastUpdated -> updated_at/created_at

    Everything else (`instantiatesCanonical`, `instantiatesUri`, `statusReason`, `description`,
    `location`, `reasonCode`, `reasonReference`, `insurance`, `note`, `relevantHistory`,
    `restriction`, `input`, `output`, `extension`) has no search parameter and lives only in
    `content`.

    `subject`, `focus` and `based-on` are Reference(Any): any relative `Type/<id>` is indexed with
    a plain-string type and a search by bare id is ambiguous (`subject=Type/id` or
    `subject:Type=id`); `owner` and `requester` have several targets too. `patient` is `subject`
    narrowed to Patients (a reference to another type or a logical subject counts as missing it).

    All index columns are nullable. No `user_id`: a Task is a shared tenant-level entity. No
    DB-level CHECK constraints."""

    __tablename__ = "task"
    __table_args__ = (
        Index("ix_task_authored", "authored_start", "authored_end"),
        Index("ix_task_modified", "modified_start", "modified_end"),
        Index("ix_task_period", "period_start", "period_end"),
        Index("ix_task_for_type_id", "for_type", "for_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_id = Column(
        BigInteger,
        task_id_seq,
        server_default=task_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(_enum(TaskStatus, "task_status"), nullable=True, index=True)
    intent = Column(_enum(TaskIntent, "task_intent"), nullable=True)
    priority = Column(_enum(TaskPriority, "task_priority"), nullable=True)

    # authoredOn / lastModified (dateTime) and executionPeriod: half-open [start, end) ranges.
    authored_start = Column(DateTime(timezone=True), nullable=True)
    authored_end = Column(DateTime(timezone=True), nullable=True)
    modified_start = Column(DateTime(timezone=True), nullable=True)
    modified_end = Column(DateTime(timezone=True), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # groupIdentifier (0..1 Identifier)
    group_identifier_system = Column(String, nullable=True)
    group_identifier_value = Column(String, nullable=True)

    # for (0..1 Reference(Any)) - searched as `subject`, and `patient` when it names a Patient
    for_reference = Column(String, nullable=True)
    for_type = Column(String, nullable=True)
    for_id = Column(BigInteger, nullable=True)
    for_identifier_system = Column(String, nullable=True)
    for_identifier_value = Column(String, nullable=True)

    # focus (0..1 Reference(Any))
    focus_reference = Column(String, nullable=True)
    focus_type = Column(String, nullable=True)
    focus_id = Column(BigInteger, nullable=True, index=True)
    focus_identifier_system = Column(String, nullable=True)
    focus_identifier_value = Column(String, nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(String, nullable=True)
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_identifier_system = Column(String, nullable=True)
    encounter_identifier_value = Column(String, nullable=True)

    # requester (0..1 Reference(Device | Organization | Patient | Practitioner | ...))
    requester_reference = Column(String, nullable=True)
    requester_type = Column(String, nullable=True)
    requester_id = Column(BigInteger, nullable=True, index=True)
    requester_identifier_system = Column(String, nullable=True)
    requester_identifier_value = Column(String, nullable=True)

    # owner (0..1 Reference(Practitioner | PractitionerRole | Organization | CareTeam | ...))
    owner_reference = Column(String, nullable=True)
    owner_type = Column(String, nullable=True)
    owner_id = Column(BigInteger, nullable=True, index=True)
    owner_identifier_system = Column(String, nullable=True)
    owner_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "TaskIdentifier", back_populates="task", cascade="all, delete-orphan"
    )
    tokens = relationship(
        "TaskToken", back_populates="task", cascade="all, delete-orphan"
    )
    references = relationship(
        "TaskReference", back_populates="task", cascade="all, delete-orphan"
    )
