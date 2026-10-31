from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Enum,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.goal.enums import (
    GoalExpressedByReferenceType,
    GoalLifecycleStatus,
    GoalSubjectReferenceType,
)
from app.models.shared import TenantAuditMixin


class GoalModel(TenantAuditMixin, Base):
    """SQLAlchemy ORM model for FHIR R4 Goal resource.

    Describes the intended objective(s) for a patient, group or organization care.
    Sequenced public ID block starts at 460000 (goal_pub_seq).
    There is deliberately no user_id: Goal is an org-scoped clinical entity,
    associated with a subject, not scoped to an individual system user.
    """

    __tablename__ = "goal"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_id = Column(
        BigInteger,
        Sequence(
            "goal_pub_seq",
            start=460000,
            increment=1,
            metadata=Base.metadata,
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    # lifecycleStatus (1..1 code, binding: goal-status)
    lifecycle_status = Column(
        Enum(
            GoalLifecycleStatus,
            name="goal_lifecycle_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    # achievementStatus (0..1 CodeableConcept) — text stored flat, codings in goal_achievement_status_coding
    achievement_status_text = Column(String, nullable=True)

    # priority (0..1 CodeableConcept) — text stored flat, codings in goal_priority_coding
    priority_text = Column(String, nullable=True)

    # description (1..1 CodeableConcept) — text stored flat, codings in goal_description_coding
    description_text = Column(String, nullable=True)

    # subject (1..1 Reference(Patient|Group|Organization))
    subject_reference = Column(String, nullable=False)
    subject_type = Column(
        Enum(GoalSubjectReferenceType, name="goal_subject_reference_type"),
        nullable=False,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # start[x] (0..1 date | CodeableConcept)
    start_date = Column(Date, nullable=True)
    start_codeable_concept_text = Column(String, nullable=True)

    # statusDate (0..1 date)
    status_date = Column(Date, nullable=True)

    # statusReason (0..1 string per FHIR R4)
    status_reason = Column(String, nullable=True)

    # expressedBy (0..1 Reference(Patient|Practitioner|PractitionerRole|RelatedPerson))
    expressed_by_reference = Column(String, nullable=True)
    expressed_by_type = Column(
        Enum(
            GoalExpressedByReferenceType,
            name="goal_expressed_by_reference_type",
        ),
        nullable=True,
    )
    expressed_by_id = Column(BigInteger, nullable=True, index=True)
    expressed_by_display = Column(String, nullable=True)

    # extension (0..* Extension, JSONB)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Relationships
    identifiers = relationship(
        "GoalIdentifier",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    achievement_status_codings = relationship(
        "GoalAchievementStatusCoding",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    priority_codings = relationship(
        "GoalPriorityCoding",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    description_codings = relationship(
        "GoalDescriptionCoding",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    start_codings = relationship(
        "GoalStartCoding",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    categories = relationship(
        "GoalCategory",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    targets = relationship(
        "GoalTarget",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    addresses_list = relationship(
        "GoalAddresses",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "GoalNote",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    outcome_codes = relationship(
        "GoalOutcomeCode",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    outcome_references = relationship(
        "GoalOutcomeReference",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
