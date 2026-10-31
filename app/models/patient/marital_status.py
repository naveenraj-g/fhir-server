from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class PatientMaritalStatusCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Patient.maritalStatus (0..1 CodeableConcept) coding child table.
    Per CLAUDE.md CodeableConcept storage rule: coding[] is always real 0..*
    even when CodeableConcept is 0..1, promoted to its own dedicated child table."""

    __tablename__ = "patient_marital_status_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )

    patient = relationship("PatientModel", back_populates="marital_status_codings")
