from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ConditionClinicalStatusCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Condition.clinicalStatus.coding (0..*)."""

    __tablename__ = "condition_clinical_status_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_pk = Column(
        BigInteger, ForeignKey("condition.id"), nullable=False, index=True
    )

    condition = relationship("ConditionModel", back_populates="clinical_status_codings")
