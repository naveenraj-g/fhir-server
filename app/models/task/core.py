from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Integer,
    Sequence,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import TenantAuditMixin
from app.models.task.enums import (
    TaskEncounterReferenceType,
    TaskIntent,
    TaskLocationReferenceType,
    TaskOwnerReferenceType,
    TaskPriority,
    TaskRequesterReferenceType,
    TaskStatus,
)


class TaskModel(TenantAuditMixin, Base):
    """SQLAlchemy ORM model for FHIR R4 Task resource.

    A task to be performed.
    Sequenced public ID block starts at 280000 (task_pub_seq).
    There is deliberately no user_id: Task is an org-scoped entity,
    not scoped to an individual system user.
    """

    __tablename__ = "task"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(
        BigInteger,
        Sequence(
            "task_pub_seq",
            start=280000,
            increment=1,
            metadata=Base.metadata,
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    # status (1..1 code, binding: task-status)
    status = Column(
        Enum(
            TaskStatus,
            name="task_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    # intent (1..1 code, binding: task-intent)
    intent = Column(
        Enum(
            TaskIntent,
            name="task_intent",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    # priority (0..1 code, binding: request-priority)
    priority = Column(
        Enum(
            TaskPriority,
            name="task_priority",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # description (0..1 string)
    description = Column(Text, nullable=True)

    # instantiatesCanonical (0..1 canonical(ActivityDefinition))
    instantiates_canonical = Column(String, nullable=True)

    # instantiatesUri (0..1 uri)
    instantiates_uri = Column(String, nullable=True)

    # authoredOn (0..1 dateTime)
    authored_on = Column(DateTime(timezone=True), nullable=True)

    # lastModified (0..1 dateTime)
    last_modified = Column(DateTime(timezone=True), nullable=True)

    # CodeableConcept text columns (codings live in sibling child tables)
    code_text = Column(String, nullable=True)
    status_reason_text = Column(String, nullable=True)
    business_status_text = Column(String, nullable=True)
    reason_code_text = Column(String, nullable=True)

    # focus (0..1 Reference(Any))
    focus_reference = Column(String, nullable=True)
    focus_type = Column(String, nullable=True)
    focus_id = Column(BigInteger, nullable=True, index=True)
    focus_display = Column(String, nullable=True)

    # for (0..1 Reference(Any))
    for_reference = Column(String, nullable=True)
    for_type = Column(String, nullable=True)
    for_id = Column(BigInteger, nullable=True, index=True)
    for_display = Column(String, nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(TaskEncounterReferenceType, name="task_encounter_reference_type"),
        nullable=True,
    )
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    # executionPeriod (0..1 Period)
    execution_period_start = Column(DateTime(timezone=True), nullable=True)
    execution_period_end = Column(DateTime(timezone=True), nullable=True)

    # requester (0..1 Reference(Device|Organization|Patient|Practitioner|PractitionerRole|RelatedPerson))
    requester_reference = Column(String, nullable=True)
    requester_type = Column(
        Enum(TaskRequesterReferenceType, name="task_requester_reference_type"),
        nullable=True,
    )
    requester_id = Column(BigInteger, nullable=True, index=True)
    requester_display = Column(String, nullable=True)

    # owner (0..1 Reference(Practitioner|PractitionerRole|Organization|CareTeam|HealthcareService|Patient|Device|RelatedPerson))
    owner_reference = Column(String, nullable=True)
    owner_type = Column(
        Enum(TaskOwnerReferenceType, name="task_owner_reference_type"),
        nullable=True,
    )
    owner_id = Column(BigInteger, nullable=True, index=True)
    owner_display = Column(String, nullable=True)

    # location (0..1 Reference(Location))
    location_reference = Column(String, nullable=True)
    location_type = Column(
        Enum(TaskLocationReferenceType, name="task_location_reference_type"),
        nullable=True,
    )
    location_id = Column(BigInteger, nullable=True, index=True)
    location_display = Column(String, nullable=True)

    # reasonReference (0..1 Reference(Any))
    reason_reference_reference = Column(String, nullable=True)
    reason_reference_type = Column(String, nullable=True)
    reason_reference_id = Column(BigInteger, nullable=True, index=True)
    reason_reference_display = Column(String, nullable=True)

    # groupIdentifier (0..1 Identifier)
    group_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    group_identifier_system = Column(String, nullable=True)
    group_identifier_value = Column(String, nullable=True)
    group_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    group_identifier_period_end = Column(DateTime(timezone=True), nullable=True)
    group_identifier_assigner_reference = Column(String, nullable=True)
    group_identifier_assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    group_identifier_assigner_id = Column(BigInteger, nullable=True)
    group_identifier_assigner_display = Column(String, nullable=True)

    # restriction (0..1 BackboneElement)
    restriction_repetitions = Column(Integer, nullable=True)
    restriction_period_start = Column(DateTime(timezone=True), nullable=True)
    restriction_period_end = Column(DateTime(timezone=True), nullable=True)

    # extension (0..* Extension, JSONB)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Relationships
    identifiers = relationship(
        "TaskIdentifier",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    based_on_list = relationship(
        "TaskBasedOn",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    part_of_list = relationship(
        "TaskPartOf",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    insurance_list = relationship(
        "TaskInsurance",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    relevant_history_list = relationship(
        "TaskRelevantHistory",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    restriction_recipients = relationship(
        "TaskRestrictionRecipient",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    performer_types = relationship(
        "TaskPerformerType",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    code_codings = relationship(
        "TaskCodeCoding",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    status_reason_codings = relationship(
        "TaskStatusReasonCoding",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    business_status_codings = relationship(
        "TaskBusinessStatusCoding",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    reason_code_codings = relationship(
        "TaskReasonCodeCoding",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "TaskNote",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    inputs = relationship(
        "TaskInput",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    outputs = relationship(
        "TaskOutput",
        back_populates="task",
        cascade="all, delete-orphan",
    )
