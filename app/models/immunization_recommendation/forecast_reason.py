from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationRecommendationForecastReasonModel(TenantAuditMixin, Base):
    """ImmunizationRecommendation.recommendation.forecastReason (0..* CodeableConcept) child table."""

    __tablename__ = "immunization_recommendation_forecast_reason"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    recommendation_id = Column(
        BigInteger,
        ForeignKey("immunization_recommendation_recommendation.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    recommendation = relationship(
        "ImmunizationRecommendationRecommendationModel",
        back_populates="forecast_reasons",
    )
    codings = relationship(
        "ImmunizationRecommendationForecastReasonCodingModel",
        back_populates="forecast_reason",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ImmunizationRecommendationForecastReasonCodingModel(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """ImmunizationRecommendation.recommendation.forecastReason.coding (0..* Coding) grandchild table."""

    __tablename__ = "immunization_recommendation_forecast_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    forecast_reason_id = Column(
        BigInteger,
        ForeignKey("immunization_recommendation_forecast_reason.id"),
        nullable=False,
        index=True,
    )

    forecast_reason = relationship(
        "ImmunizationRecommendationForecastReasonModel",
        back_populates="codings",
    )
