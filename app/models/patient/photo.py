from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirAttachmentMixin, TenantAuditMixin


class PatientPhoto(FhirAttachmentMixin, TenantAuditMixin, Base):
    """Patient.photo (0..*) Attachment child table."""

    __tablename__ = "patient_photo"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )

    patient = relationship("PatientModel", back_populates="photos")
