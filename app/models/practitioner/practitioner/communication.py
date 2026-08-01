from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base


class PractitionerCommunication(Base):
    __tablename__ = "practitioner_communication"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(
        Integer, ForeignKey("practitioner.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    language_system = Column(String, nullable=False)
    language_version = Column(String, nullable=True)
    language_code = Column(String, nullable=False)
    language_display = Column(String, nullable=False)
    language_text = Column(String, nullable=True)
    language_user_selected = Column(Boolean, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="communications")
