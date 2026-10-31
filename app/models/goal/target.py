from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class GoalTarget(TenantAuditMixin, Base):
    """Goal.target (0..*) BackboneElement child table."""

    __tablename__ = "goal_target"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_pk = Column(
        BigInteger, ForeignKey("goal.id"), nullable=False, index=True
    )

    # measure (0..1 CodeableConcept)
    measure_text = Column(String, nullable=True)

    # detail[x] (0..1 Quantity | Range | CodeableConcept | string | boolean | integer | Ratio)
    detail_string = Column(Text, nullable=True)
    detail_boolean = Column(Boolean, nullable=True)
    detail_integer = Column(Integer, nullable=True)

    detail_quantity_value = Column(Numeric, nullable=True)
    detail_quantity_unit = Column(String, nullable=True)
    detail_quantity_system = Column(String, nullable=True)
    detail_quantity_code = Column(String, nullable=True)
    detail_quantity_comparator = Column(String, nullable=True)

    detail_range_low_value = Column(Numeric, nullable=True)
    detail_range_low_unit = Column(String, nullable=True)
    detail_range_low_system = Column(String, nullable=True)
    detail_range_low_code = Column(String, nullable=True)
    detail_range_high_value = Column(Numeric, nullable=True)
    detail_range_high_unit = Column(String, nullable=True)
    detail_range_high_system = Column(String, nullable=True)
    detail_range_high_code = Column(String, nullable=True)

    detail_ratio_numerator_value = Column(Numeric, nullable=True)
    detail_ratio_numerator_unit = Column(String, nullable=True)
    detail_ratio_numerator_system = Column(String, nullable=True)
    detail_ratio_numerator_code = Column(String, nullable=True)
    detail_ratio_denominator_value = Column(Numeric, nullable=True)
    detail_ratio_denominator_unit = Column(String, nullable=True)
    detail_ratio_denominator_system = Column(String, nullable=True)
    detail_ratio_denominator_code = Column(String, nullable=True)

    detail_codeable_concept_text = Column(String, nullable=True)

    # due[x] (0..1 date | Duration)
    due_date = Column(Date, nullable=True)
    due_duration_value = Column(Numeric, nullable=True)
    due_duration_unit = Column(String, nullable=True)
    due_duration_system = Column(String, nullable=True)
    due_duration_code = Column(String, nullable=True)

    goal = relationship("GoalModel", back_populates="targets")
    measure_codings = relationship(
        "GoalTargetMeasureCoding",
        back_populates="target",
        cascade="all, delete-orphan",
    )
    detail_codings = relationship(
        "GoalTargetDetailCoding",
        back_populates="target",
        cascade="all, delete-orphan",
    )


class GoalTargetMeasureCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Goal.target.measure.coding (0..*) grandchild table."""

    __tablename__ = "goal_target_measure_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_target_id = Column(
        BigInteger,
        ForeignKey("goal_target.id"),
        nullable=False,
        index=True,
    )

    target = relationship("GoalTarget", back_populates="measure_codings")


class GoalTargetDetailCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Goal.target.detailCodeableConcept.coding (0..*) grandchild table."""

    __tablename__ = "goal_target_detail_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_target_id = Column(
        BigInteger,
        ForeignKey("goal_target.id"),
        nullable=False,
        index=True,
    )

    target = relationship("GoalTarget", back_populates="detail_codings")
