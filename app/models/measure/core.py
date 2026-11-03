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
from app.models.enums import IdentifierUse
from app.models.measure.enums import (
    MeasureStatus,
    MeasureSubjectReferenceType,
)
from app.models.shared import TenantAuditMixin

measure_pub_seq = Sequence(
    "measure_pub_seq", start=560000, increment=1, metadata=Base.metadata
)


class MeasureModel(TenantAuditMixin, Base):
    """Measure resource model (FHIR R4)."""

    __tablename__ = "measure"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    measure_id = Column(
        BigInteger,
        measure_pub_seq,
        server_default=measure_pub_seq.next_value(),
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

    status = Column(
        Enum(MeasureStatus, name="measure_status"),
        nullable=False,
    )
    experimental = Column(Boolean, nullable=True)

    # subject[x] (CodeableConcept | Reference(Group))
    subject_codeable_concept_text = Column(String, nullable=True)
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(
            MeasureSubjectReferenceType,
            name="measure_subject_reference_type",
        ),
        nullable=True,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # subject.identifier fallback (11 columns)
    subject_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    subject_identifier_type_system = Column(String, nullable=True)
    subject_identifier_type_version = Column(String, nullable=True)
    subject_identifier_type_code = Column(String, nullable=True)
    subject_identifier_type_display = Column(String, nullable=True)
    subject_identifier_type_user_selected = Column(Boolean, nullable=True)
    subject_identifier_type_text = Column(String, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)
    subject_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    subject_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

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
    disclaimer = Column(Text, nullable=True)

    # scoring (0..1 CodeableConcept)
    scoring_text = Column(String, nullable=True)

    # compositeScoring (0..1 CodeableConcept)
    composite_scoring_text = Column(String, nullable=True)

    risk_adjustment = Column(String, nullable=True)
    rate_aggregation = Column(String, nullable=True)
    rationale = Column(Text, nullable=True)
    clinical_recommendation_statement = Column(Text, nullable=True)

    # improvementNotation (0..1 CodeableConcept)
    improvement_notation_text = Column(String, nullable=True)

    definition = Column(ARRAY(String), nullable=True)
    guidance = Column(Text, nullable=True)

    # Relationships
    identifiers = relationship(
        "MeasureIdentifier",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
    subject_codings = relationship(
        "MeasureSubjectCoding",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
    contacts = relationship(
        "MeasureContact",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
    use_contexts = relationship(
        "MeasureUseContext",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
    jurisdictions = relationship(
        "MeasureJurisdiction",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
    topics = relationship(
        "MeasureTopic",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
    related_artifacts = relationship(
        "MeasureRelatedArtifact",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
    scoring_codings = relationship(
        "MeasureScoringCoding",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
    composite_scoring_codings = relationship(
        "MeasureCompositeScoringCoding",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
    types = relationship(
        "MeasureType",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
    improvement_notation_codings = relationship(
        "MeasureImprovementNotationCoding",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
    groups = relationship(
        "MeasureGroup",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
    supplemental_data = relationship(
        "MeasureSupplementalData",
        back_populates="measure",
        cascade="all, delete-orphan",
    )
