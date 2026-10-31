from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirContactPointMixin, TenantAuditMixin


class PatientTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """Patient.telecom (0..*) ContactPoint child table."""

    __tablename__ = "patient_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )

    patient = relationship("PatientModel", back_populates="telecoms")
