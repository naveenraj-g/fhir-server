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


class LocationAlias(TenantAuditMixin, Base):
    """Location.alias[] — alternate names the location is or was known as.

    Column is `value`, not `alias`, matching OrganizationAlias — the sibling
    resource with the identical 0..* string-list shape.
    """

    __tablename__ = "location_alias"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named location_pk, not location_id, so it can never
    # be confused with LocationModel.location_id (the public, FHIR-facing
    # sequence ID) — same reasoning as Organization's organization_pk.
    location_pk = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )

    value = Column(String, nullable=False)

    location = relationship("LocationModel", back_populates="aliases")
