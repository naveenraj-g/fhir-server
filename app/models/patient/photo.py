from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base


class PatientPhoto(Base):
    """photo[] — Attachment — images of the patient."""

    __tablename__ = "patient_photo"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_id = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    content_type = Column(String, nullable=True)
    language = Column(String, nullable=True)
    data = Column(Text, nullable=True)
    url = Column(String, nullable=False)
    size = Column(Integer, nullable=True)
    hash = Column(String, nullable=True)
    title = Column(String, nullable=True)
    creation = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    patient = relationship("PatientModel", back_populates="photos")
