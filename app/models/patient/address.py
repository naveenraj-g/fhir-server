from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirAddressMixin, TenantAuditMixin


class PatientAddress(FhirAddressMixin, TenantAuditMixin, Base):
    """Patient.address (0..*) Address child table."""

    __tablename__ = "patient_address"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )

    patient = relationship("PatientModel", back_populates="addresses")
