from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# reasonCode (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class MedicationRequestReasonCode(TenantAuditMixin, Base):
    """One entry of MedicationRequest.reasonCode (0..* CodeableConcept) —
    coded reason, as opposed to reasonReference's resolved resource."""

    __tablename__ = "medication_request_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)
    text = Column(String, nullable=True)

    medication_request = relationship("MedicationRequestModel", back_populates="reason_codes")
    codings = relationship("MedicationRequestReasonCodeCoding", back_populates="reason_code", cascade="all, delete-orphan")


class MedicationRequestReasonCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of MedicationRequest.reasonCode.coding (0..*)."""

    __tablename__ = "medication_request_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_reason_code_id = Column(
        BigInteger, ForeignKey("medication_request_reason_code.id"), nullable=False, index=True
    )

    reason_code = relationship("MedicationRequestReasonCode", back_populates="codings")
