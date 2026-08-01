from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base


class PractitionerPhoto(Base):
    __tablename__ = "practitioner_photo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(
        Integer, ForeignKey("practitioner.id"), nullable=False, index=True
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

    practitioner = relationship("PractitionerModel", back_populates="photos")
