from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.schemas.enums import ContactPointSystem, ContactPointUse

# ---------------------------------------------------------------------------
# telecom (0..*) ContactPoint child table
# ---------------------------------------------------------------------------


class PractitionerRoleTelecom(Base):
    """telecom[] — contact details specific to the role/location/service."""

    __tablename__ = "practitioner_role_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
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

    practitioner_role = relationship("PractitionerRoleModel", back_populates="telecoms")
