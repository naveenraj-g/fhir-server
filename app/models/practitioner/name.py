from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirHumanNameMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# name (0..*) HumanName child table
# ---------------------------------------------------------------------------


class PractitionerName(FhirHumanNameMixin, TenantAuditMixin, Base):
    __tablename__ = "practitioner_name"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — see identifier.py's practitioner_pk for why this
    # isn't named practitioner_id.
    practitioner_pk = Column(
        BigInteger, ForeignKey("practitioner.id"), nullable=False, index=True
    )

    practitioner = relationship("PractitionerModel", back_populates="names")
