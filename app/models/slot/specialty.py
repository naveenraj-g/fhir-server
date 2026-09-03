from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base

# ---------------------------------------------------------------------------
# specialty (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class SlotSpecialty(Base):
    """specialty[] — the specialty of a practitioner that would be required
    to perform the service requested in this slot."""

    __tablename__ = "slot_specialty"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slot_id = Column(BigInteger, ForeignKey("slot.id"), nullable=False, index=True)
    org_id = Column(String, nullable=False)

    coding_system = Column(String, nullable=True)
    coding_version = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)
    coding_user_selected = Column(Boolean, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    slot = relationship("SlotModel", back_populates="specialties")
