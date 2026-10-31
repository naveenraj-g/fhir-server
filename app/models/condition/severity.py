from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ConditionSeverityCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Condition.severity.coding (0..*)."""

    __tablename__ = "condition_severity_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_pk = Column(
        BigInteger, ForeignKey("condition.id"), nullable=False, index=True
    )

    condition = relationship("ConditionModel", back_populates="severity_codings")
