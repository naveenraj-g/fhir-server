from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirHumanNameMixin, TenantAuditMixin


class PatientName(FhirHumanNameMixin, TenantAuditMixin, Base):
    """Patient.name (0..*) HumanName child table."""

    __tablename__ = "patient_name"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )

    patient = relationship("PatientModel", back_populates="names")
