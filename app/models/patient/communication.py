from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class PatientCommunication(TenantAuditMixin, Base):
    """Patient.communication (0..* BackboneElement) child table.
    Contains `language` (1..1 CodeableConcept) and `preferred` (0..1 boolean)."""

    __tablename__ = "patient_communication"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )
    language_text = Column(String, nullable=True)
    preferred = Column(Boolean, nullable=True)

    patient = relationship("PatientModel", back_populates="communications")
    language_codings = relationship(
        "PatientCommunicationLanguageCoding",
        back_populates="communication",
        cascade="all, delete-orphan",
    )


class PatientCommunicationLanguageCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Patient.communication.language.coding (0..*)."""

    __tablename__ = "patient_communication_language_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_communication_id = Column(
        BigInteger, ForeignKey("patient_communication.id"), nullable=False, index=True
    )

    communication = relationship("PatientCommunication", back_populates="language_codings")
