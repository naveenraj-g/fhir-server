from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin


class ImmunizationEducationModel(TenantAuditMixin, Base):
    """Immunization.education (0..* BackboneElement) child table."""

    __tablename__ = "immunization_education"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )

    document_type = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    publication_date = Column(DateTime(timezone=True), nullable=True)
    presentation_date = Column(DateTime(timezone=True), nullable=True)

    immunization = relationship("ImmunizationModel", back_populates="education_items")
