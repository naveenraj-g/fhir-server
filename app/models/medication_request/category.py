from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# category (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class MedicationRequestCategory(TenantAuditMixin, Base):
    """One entry of MedicationRequest.category (0..* CodeableConcept)."""

    __tablename__ = "medication_request_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)
    text = Column(String, nullable=True)

    medication_request = relationship("MedicationRequestModel", back_populates="categories")
    codings = relationship("MedicationRequestCategoryCoding", back_populates="category", cascade="all, delete-orphan")


class MedicationRequestCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of MedicationRequest.category.coding (0..*)."""

    __tablename__ = "medication_request_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_category_id = Column(
        BigInteger, ForeignKey("medication_request_category.id"), nullable=False, index=True
    )

    category = relationship("MedicationRequestCategory", back_populates="codings")
