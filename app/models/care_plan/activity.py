from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.care_plan.enums import (
    CarePlanActivityDetailPerformerReferenceType,
    CarePlanActivityDetailReasonReferenceType,
    CarePlanActivityKind,
    CarePlanActivityReferenceType,
    CarePlanActivityStatus,
    CarePlanAuthorReferenceType,
    CarePlanGoalReferenceType,
    CarePlanLocationReferenceType,
    CarePlanProductReferenceType,
    CarePlanQuantityComparator,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CarePlanActivity(TenantAuditMixin, Base):
    """CarePlan.activity (0..*) child table."""

    __tablename__ = "care_plan_activity"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )

    # reference (0..1 Reference)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CarePlanActivityReferenceType,
            name="care_plan_activity_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # detail (0..1 BackboneElement) flattened
    detail_kind = Column(
        Enum(CarePlanActivityKind, name="care_plan_activity_kind"),
        nullable=True,
    )
    detail_instantiates_canonical = Column(ARRAY(String), nullable=True)
    detail_instantiates_uri = Column(ARRAY(String), nullable=True)
    detail_code_text = Column(String, nullable=True)
    detail_status = Column(
        Enum(CarePlanActivityStatus, name="care_plan_activity_status"),
        nullable=True,
    )
    detail_status_reason_text = Column(String, nullable=True)
    detail_do_not_perform = Column(Boolean, nullable=True)

    # detail.scheduled[x]
    detail_scheduled_timing = Column(JSONB, nullable=True)
    detail_scheduled_period_start = Column(DateTime(timezone=True), nullable=True)
    detail_scheduled_period_end = Column(DateTime(timezone=True), nullable=True)
    detail_scheduled_string = Column(String, nullable=True)

    # detail.location (0..1 Reference(Location))
    detail_location_reference = Column(String, nullable=True)
    detail_location_type = Column(
        Enum(
            CarePlanLocationReferenceType,
            name="care_plan_location_reference_type",
        ),
        nullable=True,
    )
    detail_location_id = Column(BigInteger, nullable=True, index=True)
    detail_location_display = Column(String, nullable=True)

    # detail.product[x] (CodeableConcept | Reference)
    detail_product_codeable_concept_text = Column(String, nullable=True)
    detail_product_reference = Column(String, nullable=True)
    detail_product_type = Column(
        Enum(
            CarePlanProductReferenceType,
            name="care_plan_product_reference_type",
        ),
        nullable=True,
    )
    detail_product_id = Column(BigInteger, nullable=True, index=True)
    detail_product_display = Column(String, nullable=True)

    # detail.dailyAmount (0..1 Quantity)
    detail_daily_amount_value = Column(Numeric, nullable=True)
    detail_daily_amount_comparator = Column(
        Enum(
            CarePlanQuantityComparator,
            name="care_plan_quantity_comparator",
        ),
        nullable=True,
    )
    detail_daily_amount_unit = Column(String, nullable=True)
    detail_daily_amount_system = Column(String, nullable=True)
    detail_daily_amount_code = Column(String, nullable=True)

    # detail.quantity (0..1 Quantity)
    detail_quantity_value = Column(Numeric, nullable=True)
    detail_quantity_comparator = Column(
        Enum(
            CarePlanQuantityComparator,
            name="care_plan_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    detail_quantity_unit = Column(String, nullable=True)
    detail_quantity_system = Column(String, nullable=True)
    detail_quantity_code = Column(String, nullable=True)

    detail_description = Column(String, nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="activities")
    outcome_codeable_concepts = relationship(
        "CarePlanActivityOutcomeCC",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    outcome_references = relationship(
        "CarePlanActivityOutcomeReference",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    progress = relationship(
        "CarePlanActivityProgress",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    detail_code_codings = relationship(
        "CarePlanActivityDetailCodeCoding",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    detail_reason_codes = relationship(
        "CarePlanActivityDetailReasonCode",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    detail_reason_references = relationship(
        "CarePlanActivityDetailReasonReference",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    detail_goals = relationship(
        "CarePlanActivityDetailGoal",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    detail_status_reason_codings = relationship(
        "CarePlanActivityDetailStatusReasonCoding",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    detail_performers = relationship(
        "CarePlanActivityDetailPerformer",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    detail_product_codings = relationship(
        "CarePlanActivityDetailProductCoding",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CarePlanActivityOutcomeCC(TenantAuditMixin, Base):
    """CarePlan.activity.outcomeCodeableConcept (0..*) child table."""

    __tablename__ = "care_plan_activity_outcome_cc"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_id = Column(
        BigInteger, ForeignKey("care_plan_activity.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    activity = relationship("CarePlanActivity", back_populates="outcome_codeable_concepts")
    codings = relationship(
        "CarePlanActivityOutcomeCCCoding",
        back_populates="outcome_cc",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CarePlanActivityOutcomeCCCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """CarePlan.activity.outcomeCodeableConcept.coding (0..*) grandchild table."""

    __tablename__ = "care_plan_activity_outcome_cc_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    outcome_cc_id = Column(
        BigInteger,
        ForeignKey("care_plan_activity_outcome_cc.id"),
        nullable=False,
        index=True,
    )

    outcome_cc = relationship("CarePlanActivityOutcomeCC", back_populates="codings")


class CarePlanActivityOutcomeReference(TenantAuditMixin, Base):
    """CarePlan.activity.outcomeReference (0..*) child table."""

    __tablename__ = "care_plan_activity_outcome_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_id = Column(
        BigInteger, ForeignKey("care_plan_activity.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    activity = relationship("CarePlanActivity", back_populates="outcome_references")


class CarePlanActivityProgress(TenantAuditMixin, Base):
    """CarePlan.activity.progress (0..*) Annotation child table."""

    __tablename__ = "care_plan_activity_progress"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_id = Column(
        BigInteger, ForeignKey("care_plan_activity.id"), nullable=False, index=True
    )

    text = Column(String, nullable=False)
    time = Column(DateTime(timezone=True), nullable=True)
    author_string = Column(String, nullable=True)
    author_reference_reference = Column(String, nullable=True)
    author_reference_type = Column(
        Enum(
            CarePlanAuthorReferenceType,
            name="care_plan_author_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    author_reference_id = Column(BigInteger, nullable=True)
    author_reference_display = Column(String, nullable=True)

    activity = relationship("CarePlanActivity", back_populates="progress")


class CarePlanActivityDetailCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """CarePlan.activity.detail.code.coding (0..*) child table."""

    __tablename__ = "care_plan_activity_detail_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_id = Column(
        BigInteger, ForeignKey("care_plan_activity.id"), nullable=False, index=True
    )

    activity = relationship("CarePlanActivity", back_populates="detail_code_codings")


class CarePlanActivityDetailReasonCode(TenantAuditMixin, Base):
    """CarePlan.activity.detail.reasonCode (0..*) child table."""

    __tablename__ = "care_plan_activity_detail_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_id = Column(
        BigInteger, ForeignKey("care_plan_activity.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    activity = relationship("CarePlanActivity", back_populates="detail_reason_codes")
    codings = relationship(
        "CarePlanActivityDetailReasonCodeCoding",
        back_populates="reason_code",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CarePlanActivityDetailReasonCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """CarePlan.activity.detail.reasonCode.coding (0..*) grandchild table."""

    __tablename__ = "care_plan_activity_detail_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    reason_code_id = Column(
        BigInteger,
        ForeignKey("care_plan_activity_detail_reason_code.id"),
        nullable=False,
        index=True,
    )

    reason_code = relationship("CarePlanActivityDetailReasonCode", back_populates="codings")


class CarePlanActivityDetailReasonReference(TenantAuditMixin, Base):
    """CarePlan.activity.detail.reasonReference (0..*) child table."""

    __tablename__ = "care_plan_activity_detail_reason_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_id = Column(
        BigInteger, ForeignKey("care_plan_activity.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CarePlanActivityDetailReasonReferenceType,
            name="care_plan_activity_detail_reason_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    activity = relationship("CarePlanActivity", back_populates="detail_reason_references")


class CarePlanActivityDetailGoal(TenantAuditMixin, Base):
    """CarePlan.activity.detail.goal (0..*) child table."""

    __tablename__ = "care_plan_activity_detail_goal"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_id = Column(
        BigInteger, ForeignKey("care_plan_activity.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CarePlanGoalReferenceType,
            name="care_plan_goal_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    activity = relationship("CarePlanActivity", back_populates="detail_goals")


class CarePlanActivityDetailStatusReasonCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """CarePlan.activity.detail.statusReason.coding (0..*) child table."""

    __tablename__ = "care_plan_activity_detail_status_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_id = Column(
        BigInteger, ForeignKey("care_plan_activity.id"), nullable=False, index=True
    )

    activity = relationship("CarePlanActivity", back_populates="detail_status_reason_codings")


class CarePlanActivityDetailPerformer(TenantAuditMixin, Base):
    """CarePlan.activity.detail.performer (0..*) child table."""

    __tablename__ = "care_plan_activity_detail_performer"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_id = Column(
        BigInteger, ForeignKey("care_plan_activity.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CarePlanActivityDetailPerformerReferenceType,
            name="care_plan_activity_detail_performer_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    activity = relationship("CarePlanActivity", back_populates="detail_performers")


class CarePlanActivityDetailProductCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """CarePlan.activity.detail.productCodeableConcept.coding (0..*) child table."""

    __tablename__ = "care_plan_activity_detail_product_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_id = Column(
        BigInteger, ForeignKey("care_plan_activity.id"), nullable=False, index=True
    )

    activity = relationship("CarePlanActivity", back_populates="detail_product_codings")
