from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class RiskAssessmentReasonCodeModel(TenantAuditMixin, Base):
    """RiskAssessment.reasonCode (0..* CodeableConcept) child table."""

    __tablename__ = "risk_assessment_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    risk_assessment_pk = Column(
        BigInteger, ForeignKey("risk_assessment.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    risk_assessment = relationship(
        "RiskAssessmentModel", back_populates="reason_codes"
    )
    codings = relationship(
        "RiskAssessmentReasonCodeCodingModel",
        back_populates="reason_code",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class RiskAssessmentReasonCodeCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """RiskAssessment.reasonCode.coding (0..* Coding) grandchild table."""

    __tablename__ = "risk_assessment_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    risk_assessment_reason_code_id = Column(
        BigInteger,
        ForeignKey("risk_assessment_reason_code.id"),
        nullable=False,
        index=True,
    )

    reason_code = relationship(
        "RiskAssessmentReasonCodeModel", back_populates="codings"
    )
