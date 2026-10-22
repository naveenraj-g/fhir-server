from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirContactPointMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# telecom (0..*) ContactPoint child table
# ---------------------------------------------------------------------------


class HealthcareServiceTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """telecom[] — contacts related to the healthcare service. Uses the
    shared FhirContactPointMixin rather than hand-declared columns, same as
    OrganizationTelecom/LocationTelecom."""

    __tablename__ = "healthcare_service_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="telecoms"
    )
