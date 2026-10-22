from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# notAvailable (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class HealthcareServiceNotAvailable(TenantAuditMixin, Base):
    """notAvailable[] BackboneElement — periods when service is unavailable.

    BackboneElement fields:
      - description  (1..1 string)  reason presented to the user (required)
      - during       (0..1 Period)  date range of unavailability
    """

    __tablename__ = "healthcare_service_not_available"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )

    description = Column(String, nullable=False)  # 1..1 required
    during_start = Column(DateTime(timezone=True), nullable=True)
    during_end = Column(DateTime(timezone=True), nullable=True)

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="not_available"
    )
