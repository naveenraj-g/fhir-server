from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirAddressMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# address (0..*) Address child table
# ---------------------------------------------------------------------------


class PractitionerAddress(FhirAddressMixin, TenantAuditMixin, Base):
    __tablename__ = "practitioner_address"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_pk = Column(
        BigInteger, ForeignKey("practitioner.id"), nullable=False, index=True
    )

    practitioner = relationship("PractitionerModel", back_populates="addresses")
