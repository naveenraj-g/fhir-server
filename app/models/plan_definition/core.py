from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Sequence,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.plan_definition.enums import (
    PlanDefinitionStatus,
    PlanDefinitionSubjectReferenceType,
)
from app.models.shared import TenantAuditMixin

plan_definition_pub_seq = Sequence(
    "plan_definition_pub_seq", start=420000, increment=1, metadata=Base.metadata
)


class PlanDefinitionModel(TenantAuditMixin, Base):
    """PlanDefinition resource model (FHIR R4)."""

    __tablename__ = "plan_definition"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    plan_definition_id = Column(
        BigInteger,
        plan_definition_pub_seq,
        server_default=plan_definition_pub_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )


    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    url = Column(String, nullable=True)
    version = Column(String, nullable=True)
    name = Column(String, nullable=True)
    title = Column(String, nullable=True)
    subtitle = Column(String, nullable=True)

    # type (0..1 CodeableConcept)
    type_text = Column(String, nullable=True)

    status = Column(
        Enum(PlanDefinitionStatus, name="plan_definition_status"),
        nullable=False,
    )
    experimental = Column(Boolean, nullable=True)

    # subject[x] (CodeableConcept | Reference(Group))
    subject_codeable_concept_text = Column(String, nullable=True)
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(
            PlanDefinitionSubjectReferenceType,
            name="plan_definition_subject_reference_type",
        ),
        nullable=True,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    date = Column(DateTime(timezone=True), nullable=True)
    publisher = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    purpose = Column(Text, nullable=True)
    usage = Column(Text, nullable=True)
    copyright = Column(Text, nullable=True)
    approval_date = Column(Date, nullable=True)
    last_review_date = Column(Date, nullable=True)

    effective_period_start = Column(DateTime(timezone=True), nullable=True)
    effective_period_end = Column(DateTime(timezone=True), nullable=True)

    library = Column(ARRAY(String), nullable=True)

    # Relationships
    identifiers = relationship(
        "PlanDefinitionIdentifier",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
    type_codings = relationship(
        "PlanDefinitionTypeCoding",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
    subject_codings = relationship(
        "PlanDefinitionSubjectCoding",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
    contacts = relationship(
        "PlanDefinitionContact",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
    use_contexts = relationship(
        "PlanDefinitionUseContext",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
    jurisdictions = relationship(
        "PlanDefinitionJurisdiction",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
    topics = relationship(
        "PlanDefinitionTopic",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
    related_artifacts = relationship(
        "PlanDefinitionRelatedArtifact",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
    goals = relationship(
        "PlanDefinitionGoal",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
    actions = relationship(
        "PlanDefinitionAction",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
