from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.observation.enums import ObservationQuantityComparator
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# component (0..*) BackboneElement — mirrors the root resource's own
# code/value[x]/dataAbsentReason/interpretation/referenceRange shapes,
# field-for-field, but FK'd to the component row instead of the root.
# ---------------------------------------------------------------------------


class ObservationComponent(TenantAuditMixin, Base):
    """Observation.component (0..*). `code` (1..1 CodeableConcept) and
    `dataAbsentReason` (0..1 CodeableConcept) are flattened with `_text`
    here, each with its own direct-child coding table. `value[x]` reuses
    the identical 11-variant flattening shape as the root resource's own
    `value[x]` (see ObservationModel's docstring)."""

    __tablename__ = "observation_component"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    observation_pk = Column(BigInteger, ForeignKey("observation.id"), nullable=False, index=True)

    # ── code (1..1 CodeableConcept) ─────────────────────────────────────────
    code_text = Column(String, nullable=True)

    # ── value[x] (0..1 choice: 11 variants, same shape as the root) ───────
    value_quantity_value = Column(Numeric, nullable=True)
    value_quantity_comparator = Column(
        Enum(ObservationQuantityComparator, name="observation_quantity_comparator", create_type=False), nullable=True
    )
    value_quantity_unit = Column(String, nullable=True)
    value_quantity_system = Column(String, nullable=True)
    value_quantity_code = Column(String, nullable=True)

    value_codeable_concept_text = Column(String, nullable=True)

    value_string = Column(String, nullable=True)
    value_boolean = Column(Boolean, nullable=True)
    value_integer = Column(Integer, nullable=True)

    value_range_low_value = Column(Numeric, nullable=True)
    value_range_low_unit = Column(String, nullable=True)
    value_range_low_system = Column(String, nullable=True)
    value_range_low_code = Column(String, nullable=True)
    value_range_high_value = Column(Numeric, nullable=True)
    value_range_high_unit = Column(String, nullable=True)
    value_range_high_system = Column(String, nullable=True)
    value_range_high_code = Column(String, nullable=True)

    value_ratio_numerator_value = Column(Numeric, nullable=True)
    value_ratio_numerator_comparator = Column(
        Enum(ObservationQuantityComparator, name="observation_quantity_comparator", create_type=False), nullable=True
    )
    value_ratio_numerator_unit = Column(String, nullable=True)
    value_ratio_numerator_system = Column(String, nullable=True)
    value_ratio_numerator_code = Column(String, nullable=True)
    value_ratio_denominator_value = Column(Numeric, nullable=True)
    value_ratio_denominator_comparator = Column(
        Enum(ObservationQuantityComparator, name="observation_quantity_comparator", create_type=False), nullable=True
    )
    value_ratio_denominator_unit = Column(String, nullable=True)
    value_ratio_denominator_system = Column(String, nullable=True)
    value_ratio_denominator_code = Column(String, nullable=True)

    value_sampled_data_origin_value = Column(Numeric, nullable=True)
    value_sampled_data_origin_unit = Column(String, nullable=True)
    value_sampled_data_origin_system = Column(String, nullable=True)
    value_sampled_data_origin_code = Column(String, nullable=True)
    value_sampled_data_period = Column(Numeric, nullable=True)
    value_sampled_data_factor = Column(Numeric, nullable=True)
    value_sampled_data_lower_limit = Column(Numeric, nullable=True)
    value_sampled_data_upper_limit = Column(Numeric, nullable=True)
    value_sampled_data_dimensions = Column(Integer, nullable=True)
    value_sampled_data_data = Column(Text, nullable=True)

    value_time = Column(Time, nullable=True)
    value_date_time = Column(DateTime(timezone=True), nullable=True)
    value_period_start = Column(DateTime(timezone=True), nullable=True)
    value_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── dataAbsentReason (0..1 CodeableConcept) ────────────────────────────
    data_absent_reason_text = Column(String, nullable=True)

    observation = relationship("ObservationModel", back_populates="components")
    code_codings = relationship(
        "ObservationComponentCodeCoding", back_populates="component", cascade="all, delete-orphan"
    )
    value_codeable_concept_codings = relationship(
        "ObservationComponentValueCodeableConceptCoding", back_populates="component", cascade="all, delete-orphan"
    )
    data_absent_reason_codings = relationship(
        "ObservationComponentDataAbsentReasonCoding", back_populates="component", cascade="all, delete-orphan"
    )
    interpretations = relationship(
        "ObservationComponentInterpretation", back_populates="component", cascade="all, delete-orphan"
    )
    reference_ranges = relationship(
        "ObservationComponentReferenceRange", back_populates="component", cascade="all, delete-orphan"
    )


class ObservationComponentCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.component.code.coding (0..*)."""

    __tablename__ = "observation_component_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_component_id = Column(
        BigInteger, ForeignKey("observation_component.id"), nullable=False, index=True
    )

    component = relationship("ObservationComponent", back_populates="code_codings")


class ObservationComponentValueCodeableConceptCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.component.valueCodeableConcept.coding (0..*)."""

    __tablename__ = "observation_component_value_codeable_concept_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_component_id = Column(
        BigInteger, ForeignKey("observation_component.id"), nullable=False, index=True
    )

    component = relationship("ObservationComponent", back_populates="value_codeable_concept_codings")


class ObservationComponentDataAbsentReasonCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.component.dataAbsentReason.coding (0..*)."""

    __tablename__ = "observation_component_data_absent_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_component_id = Column(
        BigInteger, ForeignKey("observation_component.id"), nullable=False, index=True
    )

    component = relationship("ObservationComponent", back_populates="data_absent_reason_codings")


class ObservationComponentInterpretation(TenantAuditMixin, Base):
    """One entry of Observation.component.interpretation (0..* CodeableConcept)."""

    __tablename__ = "observation_component_interpretation"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_component_id = Column(
        BigInteger, ForeignKey("observation_component.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    component = relationship("ObservationComponent", back_populates="interpretations")
    codings = relationship(
        "ObservationComponentInterpretationCoding", back_populates="interpretation", cascade="all, delete-orphan"
    )


class ObservationComponentInterpretationCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.component.interpretation.coding (0..*)."""

    __tablename__ = "observation_component_interpretation_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_component_interpretation_id = Column(
        BigInteger, ForeignKey("observation_component_interpretation.id"), nullable=False, index=True
    )

    interpretation = relationship("ObservationComponentInterpretation", back_populates="codings")


# ---------------------------------------------------------------------------
# component.referenceRange (0..*) — same structure as the root resource's
# own referenceRange (see observation/reference_range.py), FK'd to the
# component row instead.
# ---------------------------------------------------------------------------


class ObservationComponentReferenceRange(TenantAuditMixin, Base):
    """One entry of Observation.component.referenceRange (0..*)."""

    __tablename__ = "observation_component_reference_range"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_component_id = Column(
        BigInteger, ForeignKey("observation_component.id"), nullable=False, index=True
    )

    low_value = Column(Numeric, nullable=True)
    low_unit = Column(String, nullable=True)
    low_system = Column(String, nullable=True)
    low_code = Column(String, nullable=True)

    high_value = Column(Numeric, nullable=True)
    high_unit = Column(String, nullable=True)
    high_system = Column(String, nullable=True)
    high_code = Column(String, nullable=True)

    type_text = Column(String, nullable=True)

    age_low_value = Column(Numeric, nullable=True)
    age_low_unit = Column(String, nullable=True)
    age_low_system = Column(String, nullable=True)
    age_low_code = Column(String, nullable=True)
    age_high_value = Column(Numeric, nullable=True)
    age_high_unit = Column(String, nullable=True)
    age_high_system = Column(String, nullable=True)
    age_high_code = Column(String, nullable=True)

    text = Column(String, nullable=True)

    component = relationship("ObservationComponent", back_populates="reference_ranges")
    type_codings = relationship(
        "ObservationComponentReferenceRangeTypeCoding", back_populates="reference_range", cascade="all, delete-orphan"
    )
    applies_tos = relationship(
        "ObservationComponentReferenceRangeAppliesTo", back_populates="reference_range", cascade="all, delete-orphan"
    )


class ObservationComponentReferenceRangeTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.component.referenceRange.type.coding (0..*)."""

    __tablename__ = "observation_component_reference_range_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_component_reference_range_id = Column(
        BigInteger, ForeignKey("observation_component_reference_range.id"), nullable=False, index=True
    )

    reference_range = relationship("ObservationComponentReferenceRange", back_populates="type_codings")


class ObservationComponentReferenceRangeAppliesTo(TenantAuditMixin, Base):
    """One entry of Observation.component.referenceRange.appliesTo (0..* CodeableConcept)."""

    __tablename__ = "observation_component_reference_range_applies_to"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_component_reference_range_id = Column(
        BigInteger, ForeignKey("observation_component_reference_range.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    reference_range = relationship("ObservationComponentReferenceRange", back_populates="applies_tos")
    codings = relationship(
        "ObservationComponentReferenceRangeAppliesToCoding", back_populates="applies_to", cascade="all, delete-orphan"
    )


class ObservationComponentReferenceRangeAppliesToCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.component.referenceRange.appliesTo.coding (0..*)."""

    __tablename__ = "observation_component_reference_range_applies_to_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_component_reference_range_applies_to_id = Column(
        BigInteger, ForeignKey("observation_component_reference_range_applies_to.id"), nullable=False, index=True
    )

    applies_to = relationship("ObservationComponentReferenceRangeAppliesTo", back_populates="codings")
