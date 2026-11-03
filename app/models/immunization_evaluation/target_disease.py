from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationEvaluationTargetDiseaseCodingModel(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """ImmunizationEvaluation.targetDisease.coding (0..* Coding) child table."""

    __tablename__ = "immunization_evaluation_target_disease_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_evaluation_pk = Column(
        BigInteger,
        ForeignKey("immunization_evaluation.id"),
        nullable=False,
        index=True,
    )

    immunization_evaluation = relationship(
        "ImmunizationEvaluationModel", back_populates="target_disease_codings"
    )
