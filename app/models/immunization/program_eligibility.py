from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationProgramEligibilityModel(TenantAuditMixin, Base):
    """Immunization.programEligibility (0..* CodeableConcept) child table."""

    __tablename__ = "immunization_program_eligibility"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    immunization = relationship(
        "ImmunizationModel", back_populates="program_eligibilities"
    )
    codings = relationship(
        "ImmunizationProgramEligibilityCodingModel",
        back_populates="program_eligibility",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ImmunizationProgramEligibilityCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """Immunization.programEligibility.coding (0..* Coding) grandchild table."""

    __tablename__ = "immunization_program_eligibility_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    program_eligibility_id = Column(
        BigInteger,
        ForeignKey("immunization_program_eligibility.id"),
        nullable=False,
        index=True,
    )

    program_eligibility = relationship(
        "ImmunizationProgramEligibilityModel", back_populates="codings"
    )
