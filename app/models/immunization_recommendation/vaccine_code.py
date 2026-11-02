from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationRecommendationVaccineCodeModel(TenantAuditMixin, Base):
    """ImmunizationRecommendation.recommendation.vaccineCode (0..* CodeableConcept) child table."""

    __tablename__ = "immunization_recommendation_vaccine_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    recommendation_id = Column(
        BigInteger,
        ForeignKey("immunization_recommendation_recommendation.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    recommendation = relationship(
        "ImmunizationRecommendationRecommendationModel", back_populates="vaccine_codes"
    )
    codings = relationship(
        "ImmunizationRecommendationVaccineCodeCodingModel",
        back_populates="vaccine_code",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ImmunizationRecommendationVaccineCodeCodingModel(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """ImmunizationRecommendation.recommendation.vaccineCode.coding (0..* Coding) grandchild table."""

    __tablename__ = "immunization_recommendation_vaccine_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    vaccine_code_id = Column(
        BigInteger,
        ForeignKey("immunization_recommendation_vaccine_code.id"),
        nullable=False,
        index=True,
    )

    vaccine_code = relationship(
        "ImmunizationRecommendationVaccineCodeModel", back_populates="codings"
    )
