from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# alias (0..*) child table — one row per alternative name
# ---------------------------------------------------------------------------


class OrganizationAlias(TenantAuditMixin, Base):
    __tablename__ = "organization_alias"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — see identifier.py's organization_pk for why this
    # isn't named organization_id.
    organization_pk = Column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )
    value = Column(String, nullable=False)

    organization = relationship("OrganizationModel", back_populates="aliases")
