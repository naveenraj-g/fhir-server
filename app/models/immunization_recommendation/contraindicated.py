from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationRecommendationContraindicatedCodeModel(TenantAuditMixin, Base):
    """ImmunizationRecommendation.recommendation.contraindicatedVaccineCode (0..* CodeableConcept) child table."""

    __tablename__ = "immunization_recommendation_contraindicated_code"

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
        back_populates="contraindicated_vaccine_codes",
    )
    codings = relationship(
        "ImmunizationRecommendationContraindicatedCodeCodingModel",
        back_populates="contraindicated_code",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ImmunizationRecommendationContraindicatedCodeCodingModel(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """ImmunizationRecommendation.recommendation.contraindicatedVaccineCode.coding (0..* Coding) grandchild table."""

    __tablename__ = "immunization_recommendation_contraindicated_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contraindicated_code_id = Column(
        BigInteger,
        ForeignKey("immunization_recommendation_contraindicated_code.id"),
        nullable=False,
        index=True,
    )

    contraindicated_code = relationship(
        "ImmunizationRecommendationContraindicatedCodeModel",
        back_populates="codings",
    )
