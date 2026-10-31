from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.patient.enums import PatientGeneralPractitionerReferenceType
from app.models.shared import TenantAuditMixin


class PatientGeneralPractitioner(TenantAuditMixin, Base):
    """Patient.generalPractitioner (0..* Reference(Organization | Practitioner | PractitionerRole)) child table."""

    __tablename__ = "patient_general_practitioner"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            PatientGeneralPractitionerReferenceType,
            name="patient_general_practitioner_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # Reference logical-identifier fallback
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_type_text = Column(String, nullable=True)

    patient = relationship("PatientModel", back_populates="general_practitioners")
