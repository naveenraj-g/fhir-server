from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# notAvailable (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class PractitionerRoleNotAvailable(TenantAuditMixin, Base):
    """notAvailable[] BackboneElement — the practitioner is not available
    at this role/location during this period, for the given reason.

    BackboneElement fields:
      - description  (1..1 string)  reason presented to the user (required)
      - during       (0..1 Period)  date range of unavailability
    """

    __tablename__ = "practitioner_role_not_available"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_pk = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
    )

    description = Column(String, nullable=False)  # 1..1 required
    during_start = Column(DateTime(timezone=True), nullable=True)
    during_end = Column(DateTime(timezone=True), nullable=True)

    practitioner_role = relationship(
        "PractitionerRoleModel", back_populates="not_available"
    )
