from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirContactPointMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# telecom (0..*) ContactPoint child table
# ---------------------------------------------------------------------------


class PractitionerTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """No DB-level CHECK constraint — the rank>0 (positiveInt) rule is
    enforced by the FHIR validator layer instead."""

    __tablename__ = "practitioner_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_pk = Column(
        BigInteger, ForeignKey("practitioner.id"), nullable=False, index=True
    )

    practitioner = relationship("PractitionerModel", back_populates="telecoms")
