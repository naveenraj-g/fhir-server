from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.schemas.enums import ContactPointSystem, ContactPointUse

# ---------------------------------------------------------------------------
# telecom (0..*) ContactPoint child table
# ---------------------------------------------------------------------------


class HealthcareServiceTelecom(Base):
    """telecom[] — contacts related to the healthcare service."""

    __tablename__ = "healthcare_service_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_id = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    system = Column(
        Enum(ContactPointSystem, name="contact_point_system"), nullable=False
    )
    value = Column(String, nullable=False)
    use = Column(Enum(ContactPointUse, name="contact_point_use"), nullable=True)
    rank = Column(Integer, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    healthcare_service = relationship("HealthcareServiceModel", back_populates="telecoms")
