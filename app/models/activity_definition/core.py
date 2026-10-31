from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Numeric,
    Sequence,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.activity_definition.enums import (
    ActivityDefinitionIntent,
    ActivityDefinitionKind,
    ActivityDefinitionLocationReferenceType,
    ActivityDefinitionPriority,
    ActivityDefinitionProductReferenceType,
    ActivityDefinitionQuantityComparator,
    ActivityDefinitionStatus,
    ActivityDefinitionSubjectReferenceType,
)
from app.models.shared import TenantAuditMixin

activity_definition_pub_seq = Sequence(
    "activity_definition_pub_seq",
    start=410000,
    increment=1,
    metadata=Base.metadata,
)


class ActivityDefinitionModel(TenantAuditMixin, Base):
    """FHIR R4 ActivityDefinition resource model."""

    __tablename__ = "activity_definition"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_id = Column(
        BigInteger,
        activity_definition_pub_seq,
        server_default=activity_definition_pub_seq.next_value(),
        unique=True,
        nullable=False,
        index=True,
    )
    extension = Column(JSONB, nullable=True)

    # Definitional metadata
    url = Column(String, nullable=True, index=True)
    version = Column(String, nullable=True)
    name = Column(String, nullable=True, index=True)
    title = Column(String, nullable=True)
    subtitle = Column(String, nullable=True)
    status = Column(
        Enum(ActivityDefinitionStatus, name="activity_definition_status"),
        nullable=False,
        index=True,
    )
    experimental = Column(Boolean, nullable=True)
    date = Column(DateTime(timezone=True), nullable=True)
    publisher = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    purpose = Column(Text, nullable=True)
    usage = Column(Text, nullable=True)
    copyright = Column(Text, nullable=True)
    approval_date = Column(Date, nullable=True)
    last_review_date = Column(Date, nullable=True)

    # effectivePeriod (Period)
    effective_period_start = Column(DateTime(timezone=True), nullable=True)
    effective_period_end = Column(DateTime(timezone=True), nullable=True)

    # subject[x] (CodeableConcept | Reference(Group))
    subject_codeable_concept_text = Column(String, nullable=True)
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(
            ActivityDefinitionSubjectReferenceType,
            name="activity_definition_subject_reference_type",
        ),
        nullable=True,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # library (0..* canonical(Library))
    library = Column(ARRAY(String), nullable=True)

    # Action definition
    kind = Column(
        Enum(ActivityDefinitionKind, name="activity_definition_kind"),
        nullable=True,
    )
    profile = Column(String, nullable=True)
    code_text = Column(String, nullable=True)
    intent = Column(
        Enum(ActivityDefinitionIntent, name="activity_definition_intent"),
        nullable=True,
    )
    priority = Column(
        Enum(ActivityDefinitionPriority, name="activity_definition_priority"),
        nullable=True,
    )
    do_not_perform = Column(Boolean, nullable=True)

    # timing[x] (Timing | dateTime | Age | Period | Range | Duration)
    timing_timing = Column(JSONB, nullable=True)
    timing_date_time = Column(DateTime(timezone=True), nullable=True)
    timing_age_value = Column(Numeric, nullable=True)
    timing_age_unit = Column(String, nullable=True)
    timing_age_system = Column(String, nullable=True)
    timing_age_code = Column(String, nullable=True)
    timing_period_start = Column(DateTime(timezone=True), nullable=True)
    timing_period_end = Column(DateTime(timezone=True), nullable=True)
    timing_range_low_value = Column(Numeric, nullable=True)
    timing_range_low_unit = Column(String, nullable=True)
    timing_range_high_value = Column(Numeric, nullable=True)
    timing_range_high_unit = Column(String, nullable=True)
    timing_duration_value = Column(Numeric, nullable=True)
    timing_duration_unit = Column(String, nullable=True)
    timing_duration_system = Column(String, nullable=True)
    timing_duration_code = Column(String, nullable=True)

    # location Reference(Location)
    location_reference = Column(String, nullable=True)
    location_type = Column(
        Enum(
            ActivityDefinitionLocationReferenceType,
            name="activity_definition_location_reference_type",
        ),
        nullable=True,
    )
    location_id = Column(BigInteger, nullable=True, index=True)
    location_display = Column(String, nullable=True)

    # product[x] (CodeableConcept | Reference(Medication | Substance))
    product_codeable_concept_text = Column(String, nullable=True)
    product_reference = Column(String, nullable=True)
    product_type = Column(
        Enum(
            ActivityDefinitionProductReferenceType,
            name="activity_definition_product_reference_type",
        ),
        nullable=True,
    )
    product_id = Column(BigInteger, nullable=True, index=True)
    product_display = Column(String, nullable=True)

    # quantity (SimpleQuantity)
    quantity_value = Column(Numeric, nullable=True)
    quantity_comparator = Column(
        Enum(
            ActivityDefinitionQuantityComparator,
            name="activity_definition_quantity_comparator",
        ),
        nullable=True,
    )
    quantity_unit = Column(String, nullable=True)
    quantity_system = Column(String, nullable=True)
    quantity_code = Column(String, nullable=True)

    # transform (canonical(StructureMap))
    transform = Column(String, nullable=True)

    # Relationships
    identifiers = relationship(
        "ActivityDefinitionIdentifier",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    contacts = relationship(
        "ActivityDefinitionContact",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    use_contexts = relationship(
        "ActivityDefinitionUseContext",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    jurisdictions = relationship(
        "ActivityDefinitionJurisdiction",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    topics = relationship(
        "ActivityDefinitionTopic",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    body_sites = relationship(
        "ActivityDefinitionBodySite",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    code_codings = relationship(
        "ActivityDefinitionCodeCoding",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    subject_codings = relationship(
        "ActivityDefinitionSubjectCoding",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    product_codings = relationship(
        "ActivityDefinitionProductCoding",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    related_artifacts = relationship(
        "ActivityDefinitionRelatedArtifact",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    participants = relationship(
        "ActivityDefinitionParticipant",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    dosages = relationship(
        "ActivityDefinitionDosage",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    dynamic_values = relationship(
        "ActivityDefinitionDynamicValue",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    specimen_requirements = relationship(
        "ActivityDefinitionSpecimenRequirement",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    observation_requirements = relationship(
        "ActivityDefinitionObservationRequirement",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
    observation_result_requirements = relationship(
        "ActivityDefinitionObservationResultRequirement",
        back_populates="activity_definition",
        cascade="all, delete-orphan",
    )
