from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirContactPointMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# telecom (0..*) ContactPoint child table
# ---------------------------------------------------------------------------


class OrganizationTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """No DB-level CHECK constraints — org-3 ("no home-use telecom") and the
    rank>0 (positiveInt) rule are both enforced by the FHIR validator layer
    instead — see OrganizationModel's docstring (core.py) for why."""

    __tablename__ = "organization_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — see identifier.py's organization_pk for why this
    # isn't named organization_id.
    organization_pk = Column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )

    organization = relationship("OrganizationModel", back_populates="telecoms")
