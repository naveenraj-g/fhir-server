from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationVaccineCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """Immunization.vaccineCode.coding (0..* Coding) child table."""

    __tablename__ = "immunization_vaccine_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )

    immunization = relationship(
        "ImmunizationModel", back_populates="vaccine_codings"
    )
