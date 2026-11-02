from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class RiskAssessmentPredictionModel(TenantAuditMixin, Base):
    """RiskAssessment.prediction (0..* BackboneElement) child table."""

    __tablename__ = "risk_assessment_prediction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    risk_assessment_pk = Column(
        BigInteger, ForeignKey("risk_assessment.id"), nullable=False, index=True
    )

    # outcome (0..1 CodeableConcept)
    outcome_text = Column(String, nullable=True)

    # probability[x] (0..1 decimal | Range)
    probability_decimal = Column(Numeric, nullable=True)
    probability_range_low_value = Column(Numeric, nullable=True)
    probability_range_low_unit = Column(String, nullable=True)
    probability_range_low_system = Column(String, nullable=True)
    probability_range_low_code = Column(String, nullable=True)
    probability_range_high_value = Column(Numeric, nullable=True)
    probability_range_high_unit = Column(String, nullable=True)
    probability_range_high_system = Column(String, nullable=True)
    probability_range_high_code = Column(String, nullable=True)

    # qualitativeRisk (0..1 CodeableConcept)
    qualitative_risk_text = Column(String, nullable=True)

    # relativeRisk (0..1 decimal)
    relative_risk = Column(Numeric, nullable=True)

    # when[x] (0..1 Period | Range)
    when_period_start = Column(DateTime(timezone=True), nullable=True)
    when_period_end = Column(DateTime(timezone=True), nullable=True)
    when_range_low_value = Column(Numeric, nullable=True)
    when_range_low_unit = Column(String, nullable=True)
    when_range_low_system = Column(String, nullable=True)
    when_range_low_code = Column(String, nullable=True)
    when_range_high_value = Column(Numeric, nullable=True)
    when_range_high_unit = Column(String, nullable=True)
    when_range_high_system = Column(String, nullable=True)
    when_range_high_code = Column(String, nullable=True)

    # rationale (0..1 string)
    rationale = Column(Text, nullable=True)

    risk_assessment = relationship(
        "RiskAssessmentModel", back_populates="predictions"
    )
    outcome_codings = relationship(
        "RiskAssessmentPredOutcomeCodingModel",
        back_populates="prediction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    qualitative_risk_codings = relationship(
        "RiskAssessmentPredQualRiskCodingModel",
        back_populates="prediction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class RiskAssessmentPredOutcomeCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """risk_assessment_prediction.outcome.coding (0..* Coding) grandchild table."""

    __tablename__ = "risk_assessment_pred_outcome_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    risk_assessment_prediction_id = Column(
        BigInteger,
        ForeignKey("risk_assessment_prediction.id"),
        nullable=False,
        index=True,
    )

    prediction = relationship(
        "RiskAssessmentPredictionModel", back_populates="outcome_codings"
    )


class RiskAssessmentPredQualRiskCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """risk_assessment_prediction.qualitativeRisk.coding (0..* Coding) grandchild table."""

    __tablename__ = "risk_assessment_pred_qual_risk_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    risk_assessment_prediction_id = Column(
        BigInteger,
        ForeignKey("risk_assessment_prediction.id"),
        nullable=False,
        index=True,
    )

    prediction = relationship(
        "RiskAssessmentPredictionModel", back_populates="qualitative_risk_codings"
    )
