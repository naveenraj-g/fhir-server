from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.patient.enums import ContactPointSystem, ContactPointUse


class PatientTelecom(Base):
    """telecom[] — ContactPoint — contact details for the patient."""

    __tablename__ = "patient_telecom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    system = Column(
        Enum(ContactPointSystem, name="contact_point_system"), nullable=False
    )
    value = Column(String, nullable=False)
    use = Column(Enum(ContactPointUse, name="contact_point_use"), nullable=True)
    rank = Column(Integer, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    patient = relationship("PatientModel", back_populates="telecoms")
