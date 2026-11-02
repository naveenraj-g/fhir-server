from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationRecommendationDateCriterionModel(TenantAuditMixin, Base):
    """ImmunizationRecommendation.recommendation.dateCriterion (0..* BackboneElement) child table."""

    __tablename__ = "immunization_recommendation_date_criterion"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    recommendation_id = Column(
        BigInteger,
        ForeignKey("immunization_recommendation_recommendation.id"),
        nullable=False,
        index=True,
    )

    code_text = Column(String, nullable=True)
    value = Column(DateTime(timezone=True), nullable=False)

    recommendation = relationship(
        "ImmunizationRecommendationRecommendationModel",
        back_populates="date_criteria",
    )
    code_codings = relationship(
        "ImmunizationRecommendationDateCriterionCodeCodingModel",
        back_populates="date_criterion",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ImmunizationRecommendationDateCriterionCodeCodingModel(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """ImmunizationRecommendation.recommendation.dateCriterion.code.coding (0..* Coding) grandchild table."""

    __tablename__ = "immunization_recommendation_date_criterion_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date_criterion_id = Column(
        BigInteger,
        ForeignKey("immunization_recommendation_date_criterion.id"),
        nullable=False,
        index=True,
    )

    date_criterion = relationship(
        "ImmunizationRecommendationDateCriterionModel",
        back_populates="code_codings",
    )
