from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin


class ImmunizationRecommendationRecommendationModel(TenantAuditMixin, Base):
    """ImmunizationRecommendation.recommendation (1..* BackboneElement) child table."""

    __tablename__ = "immunization_recommendation_recommendation"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_recommendation_pk = Column(
        BigInteger,
        ForeignKey("immunization_recommendation.id"),
        nullable=False,
        index=True,
    )

    # targetDisease (0..1 CodeableConcept) — text flattened
    target_disease_text = Column(String, nullable=True)

    # forecastStatus (1..1 CodeableConcept) — text flattened
    forecast_status_text = Column(String, nullable=True)

    # description (0..1 string)
    description = Column(String, nullable=True)

    # series (0..1 string)
    series = Column(String, nullable=True)

    # doseNumber[x] (0..1 positiveInt | string)
    dose_number_positive_int = Column(Integer, nullable=True)
    dose_number_string = Column(String, nullable=True)

    # seriesDoses[x] (0..1 positiveInt | string)
    series_doses_positive_int = Column(Integer, nullable=True)
    series_doses_string = Column(String, nullable=True)

    # Relationships
    immunization_recommendation = relationship(
        "ImmunizationRecommendationModel",
        back_populates="recommendations",
    )
    vaccine_codes = relationship(
        "ImmunizationRecommendationVaccineCodeModel",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    target_disease_codings = relationship(
        "ImmunizationRecommendationTargetDiseaseCodingModel",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    contraindicated_vaccine_codes = relationship(
        "ImmunizationRecommendationContraindicatedCodeModel",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    forecast_status_codings = relationship(
        "ImmunizationRecommendationForecastStatusCodingModel",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    forecast_reasons = relationship(
        "ImmunizationRecommendationForecastReasonModel",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    date_criteria = relationship(
        "ImmunizationRecommendationDateCriterionModel",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    supporting_immunizations = relationship(
        "ImmunizationRecommendationSupportingImmunizationModel",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    supporting_patient_information = relationship(
        "ImmunizationRecommendationSupportingPatientInformationModel",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
