from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base

# ---------------------------------------------------------------------------
# type (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class LocationType(Base):
    """Location.type[] — the function performed at the location
    (v3.ServiceDeliveryLocationRoleType, extensible binding).

    Standard CodeableConcept[] child shape: one flattened coding plus the
    concept's own text, identical to OrganizationType.
    """

    __tablename__ = "location_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    location_id = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    coding_system = Column(String, nullable=True)
    coding_version = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)
    coding_user_selected = Column(Boolean, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    location = relationship("LocationModel", back_populates="types")
