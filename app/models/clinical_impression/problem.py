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

from .enums import ClinicalImpressionProblemReferenceType


class ClinicalImpressionProblemModel(TenantAuditMixin, Base):
    """ClinicalImpression.problem (0..* Reference(Condition | AllergyIntolerance)) child table."""

    __tablename__ = "clinical_impression_problem"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_pk = Column(
        BigInteger, ForeignKey("clinical_impression.id"), nullable=False, index=True
    )

    problem_reference = Column(String, nullable=True)
    problem_type = Column(
        Enum(
            ClinicalImpressionProblemReferenceType,
            name="clinical_impression_problem_reference_type",
        ),
        nullable=True,
    )
    problem_id = Column(BigInteger, nullable=True, index=True)
    problem_display = Column(String, nullable=True)

    # problem.identifier fallback (11 columns)
    problem_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    problem_identifier_type_system = Column(String, nullable=True)
    problem_identifier_type_version = Column(String, nullable=True)
    problem_identifier_type_code = Column(String, nullable=True)
    problem_identifier_type_display = Column(String, nullable=True)
    problem_identifier_type_user_selected = Column(Boolean, nullable=True)
    problem_identifier_type_text = Column(String, nullable=True)
    problem_identifier_system = Column(String, nullable=True)
    problem_identifier_value = Column(String, nullable=True)
    problem_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    problem_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    clinical_impression = relationship(
        "ClinicalImpressionModel", back_populates="problems"
    )
