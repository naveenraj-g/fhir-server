from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirContactPointMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# telecom (0..*) ContactPoint child table
# ---------------------------------------------------------------------------


class PractitionerRoleTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """telecom[] — contact details specific to the role/location while this
    practitioner performs it. Uses the shared FhirContactPointMixin rather
    than hand-declared columns, same as HealthcareServiceTelecom."""

    __tablename__ = "practitioner_role_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_pk = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
    )

    practitioner_role = relationship(
        "PractitionerRoleModel", back_populates="telecoms"
    )
