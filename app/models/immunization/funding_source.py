from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationFundingSourceCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """Immunization.fundingSource.coding (0..* Coding) child table."""

    __tablename__ = "immunization_funding_source_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )

    immunization = relationship(
        "ImmunizationModel", back_populates="funding_source_codings"
    )
