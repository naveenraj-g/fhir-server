from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationStatusReasonCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """Immunization.statusReason.coding (0..* Coding) child table."""

    __tablename__ = "immunization_status_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )

    immunization = relationship(
        "ImmunizationModel", back_populates="status_reason_codings"
    )
