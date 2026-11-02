from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationSiteCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """Immunization.site.coding (0..* Coding) child table."""

    __tablename__ = "immunization_site_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )

    immunization = relationship(
        "ImmunizationModel", back_populates="site_codings"
    )
