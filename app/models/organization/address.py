from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirAddressMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# address (0..*) Address child table
# ---------------------------------------------------------------------------


class OrganizationAddress(FhirAddressMixin, TenantAuditMixin, Base):
    """No DB-level CHECK constraint — org-2 ("no home-use address") is
    enforced by the FHIR validator layer instead — see OrganizationModel's
    docstring (core.py) for why."""

    __tablename__ = "organization_address"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — see identifier.py's organization_pk for why this
    # isn't named organization_id.
    organization_pk = Column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )

    organization = relationship("OrganizationModel", back_populates="addresses")
