from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ClinicalImpressionStatusReasonCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """ClinicalImpression.statusReason.coding (0..* Coding) child table."""

    __tablename__ = "clinical_impression_status_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_pk = Column(
        BigInteger, ForeignKey("clinical_impression.id"), nullable=False, index=True
    )

    clinical_impression = relationship(
        "ClinicalImpressionModel", back_populates="status_reason_codings"
    )
