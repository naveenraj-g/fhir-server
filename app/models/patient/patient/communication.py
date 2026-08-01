from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base


class PatientCommunication(Base):
    """communication[] BackboneElement — languages the patient can use for healthcare.

    language (1..1 CodeableConcept) — flattened; preferred (0..1 boolean).
    """

    __tablename__ = "patient_communication"
    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "language_system",
            "language_code",
            name="uq_patient_communication_language",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    language_system = Column(String, nullable=False)
    language_version = Column(String, nullable=True)
    language_code = Column(String, nullable=False)
    language_display = Column(String, nullable=False)
    language_text = Column(String, nullable=True)
    language_user_selected = Column(Boolean, nullable=True)
    preferred = Column(Boolean, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    patient = relationship("PatientModel", back_populates="communications")
