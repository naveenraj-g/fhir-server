from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base

# ---------------------------------------------------------------------------
# notAvailable (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class PractitionerRoleNotAvailable(Base):
    """notAvailable[] BackboneElement — periods when the role is unavailable.

    BackboneElement fields:
      - description  (1..1 string)  reason presented to the user (required)
      - during       (0..1 Period)  date range of unavailability
    """

    __tablename__ = "practitioner_role_not_available"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    description = Column(String, nullable=False)  # 1..1 required
    during_start = Column(DateTime(timezone=True), nullable=True)
    during_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    practitioner_role = relationship(
        "PractitionerRoleModel", back_populates="not_available"
    )
