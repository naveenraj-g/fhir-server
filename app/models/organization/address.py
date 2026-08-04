from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.schemas.enums import AddressType, AddressUse

# ---------------------------------------------------------------------------
# address (0..*) Address child table
# ---------------------------------------------------------------------------


class OrganizationAddress(Base):
    __tablename__ = "organization_address"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer, ForeignKey("organization.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)
    use = Column(Enum(AddressUse, name="address_use"), nullable=True)
    type = Column(Enum(AddressType, name="address_type"), nullable=False)
    text = Column(String, nullable=True)
    line = Column(Text, nullable=True)  # comma-separated (Address.line[] exception)
    city = Column(String, nullable=False)
    district = Column(String, nullable=True)
    state = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    country = Column(String, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    organization = relationship("OrganizationModel", back_populates="addresses")
