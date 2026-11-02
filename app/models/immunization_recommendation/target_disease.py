from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationRecommendationTargetDiseaseCodingModel(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """ImmunizationRecommendation.recommendation.targetDisease.coding (0..* Coding) child table."""

    __tablename__ = "immunization_recommendation_target_disease_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    recommendation_id = Column(
        BigInteger,
        ForeignKey("immunization_recommendation_recommendation.id"),
        nullable=False,
        index=True,
    )

    recommendation = relationship(
        "ImmunizationRecommendationRecommendationModel",
        back_populates="target_disease_codings",
    )
