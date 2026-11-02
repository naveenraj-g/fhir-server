from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin


class RiskAssessmentBasisModel(TenantAuditMixin, Base):
    """RiskAssessment.basis (0..* Reference(Any)) child table."""

    __tablename__ = "risk_assessment_basis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    risk_assessment_pk = Column(
        BigInteger, ForeignKey("risk_assessment.id"), nullable=False, index=True
    )

    # Core Reference columns (open reference: type is String)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # Reference.identifier fallback columns (11 columns)
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    risk_assessment = relationship(
        "RiskAssessmentModel", back_populates="basis"
    )
