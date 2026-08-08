from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base

# ---------------------------------------------------------------------------
# alias (0..*) child table — one row per alternative name
# ---------------------------------------------------------------------------


class LocationAlias(Base):
    """Location.alias[] — alternate names the location is or was known as.

    Column is `value`, not `alias`, matching OrganizationAlias — the sibling
    resource with the identical 0..* string-list shape.
    """

    __tablename__ = "location_alias"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    location_id = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    value = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    location = relationship("LocationModel", back_populates="aliases")
