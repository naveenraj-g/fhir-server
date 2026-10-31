from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.condition.enums import ConditionStageAssessmentReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ConditionStage(TenantAuditMixin, Base):
    """One entry of Condition.stage (0..* BackboneElement)."""

    __tablename__ = "condition_stage"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_pk = Column(
        BigInteger, ForeignKey("condition.id"), nullable=False, index=True
    )

    summary_text = Column(String, nullable=True)
    type_text = Column(String, nullable=True)

    condition = relationship("ConditionModel", back_populates="stages")
    summary_codings = relationship(
        "ConditionStageSummaryCoding",
        back_populates="stage",
        cascade="all, delete-orphan",
    )
    type_codings = relationship(
        "ConditionStageTypeCoding",
        back_populates="stage",
        cascade="all, delete-orphan",
    )
    assessments = relationship(
        "ConditionStageAssessment",
        back_populates="stage",
        cascade="all, delete-orphan",
    )


class ConditionStageSummaryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Condition.stage.summary.coding (0..*)."""

    __tablename__ = "condition_stage_summary_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_stage_id = Column(
        BigInteger, ForeignKey("condition_stage.id"), nullable=False, index=True
    )

    stage = relationship("ConditionStage", back_populates="summary_codings")


class ConditionStageTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Condition.stage.type.coding (0..*)."""

    __tablename__ = "condition_stage_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_stage_id = Column(
        BigInteger, ForeignKey("condition_stage.id"), nullable=False, index=True
    )

    stage = relationship("ConditionStage", back_populates="type_codings")


class ConditionStageAssessment(TenantAuditMixin, Base):
    """One entry of Condition.stage.assessment (0..* Reference(ClinicalImpression | DiagnosticReport | Observation))."""

    __tablename__ = "condition_stage_assessment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_stage_id = Column(
        BigInteger, ForeignKey("condition_stage.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            ConditionStageAssessmentReferenceType,
            name="condition_stage_assessment_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # Reference identifier fallback
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)

    stage = relationship("ConditionStage", back_populates="assessments")
