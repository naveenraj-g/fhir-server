from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# reasonCode (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class AppointmentReasonCode(TenantAuditMixin, Base):
    """reasonCode[] — the coded reason for the appointment, as determined
    by the requester. `text` stays flattened (sibling of coding[], not part
    of it); `coding[]` itself is a real 0..* child table
    (AppointmentReasonCodeCoding, below) — same reasoning as every other
    CodeableConcept list's coding[] promotion in this codebase."""

    __tablename__ = "appointment_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="reason_codes")
    codings = relationship(
        "AppointmentReasonCodeCoding",
        back_populates="reason_code",
        cascade="all, delete-orphan",
    )


class AppointmentReasonCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Appointment.reasonCode.coding (0..*)."""

    __tablename__ = "appointment_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_reason_code_id = Column(
        BigInteger, ForeignKey("appointment_reason_code.id"), nullable=False, index=True
    )

    reason_code = relationship("AppointmentReasonCode", back_populates="codings")
