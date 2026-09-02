from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base

# ---------------------------------------------------------------------------
# eligibility (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class HealthcareServiceEligibility(Base):
    """eligibility[] BackboneElement — eligibility requirements for the service.

    BackboneElement fields:
      - code     (0..1 CodeableConcept)  eligibility classification
      - comment  (0..1 markdown)         explanation of the requirement
    """

    __tablename__ = "healthcare_service_eligibility"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_id = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    # code (0..1 CodeableConcept)
    code_system = Column(String, nullable=True)
    code_version = Column(String, nullable=True)
    code_code = Column(String, nullable=True)
    code_display = Column(String, nullable=True)
    code_text = Column(String, nullable=True)
    code_user_selected = Column(Boolean, nullable=True)

    # comment (0..1 markdown)
    comment = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    healthcare_service = relationship("HealthcareServiceModel", back_populates="eligibilities")
