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


class OrganizationAlias(Base):
    __tablename__ = "organization_alias"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)
    value = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    organization = relationship("OrganizationModel", back_populates="aliases")
