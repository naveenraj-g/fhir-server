from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class RiskAssessmentMethodCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """RiskAssessment.method.coding (0..* Coding) child table."""

    __tablename__ = "risk_assessment_method_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    risk_assessment_pk = Column(
        BigInteger, ForeignKey("risk_assessment.id"), nullable=False, index=True
    )

    risk_assessment = relationship(
        "RiskAssessmentModel", back_populates="method_codings"
    )
