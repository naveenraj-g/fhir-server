from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationRecommendationForecastStatusCodingModel(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """ImmunizationRecommendation.recommendation.forecastStatus.coding (0..* Coding) child table."""

    __tablename__ = "immunization_recommendation_forecast_status_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    recommendation_id = Column(
        BigInteger,
        ForeignKey("immunization_recommendation_recommendation.id"),
        nullable=False,
        index=True,
    )

    recommendation = relationship(
        "ImmunizationRecommendationRecommendationModel",
        back_populates="forecast_status_codings",
    )
