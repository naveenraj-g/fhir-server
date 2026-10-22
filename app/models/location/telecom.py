from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirContactPointMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# telecom (0..*) ContactPoint child table
# ---------------------------------------------------------------------------


class LocationTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """Location.telecom[] — contact details (phone, fax, email, website) for
    the location. Identical shape to OrganizationTelecom, using the same
    shared FhirContactPointMixin rather than hand-declared columns."""

    __tablename__ = "location_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named location_pk, not location_id, so it can never
    # be confused with LocationModel.location_id (the public, FHIR-facing
    # sequence ID) — same reasoning as Organization's organization_pk.
    location_pk = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )

    location = relationship("LocationModel", back_populates="telecoms")
