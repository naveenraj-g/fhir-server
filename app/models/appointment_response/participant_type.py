from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# participantType (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class AppointmentResponseParticipantType(TenantAuditMixin, Base):
    """participantType[] — role of participant in the appointment (one
    half of apr-1's "participantType.exists() or actor.exists()" — see
    AppointmentResponseModel's docstring). `text` stays flattened (sibling
    of coding[], not part of it); `coding[]` itself is a real 0..* child
    table (AppointmentResponseParticipantTypeCoding, below) — same
    reasoning as every other CodeableConcept-list promotion in this
    codebase."""

    __tablename__ = "appointment_response_participant_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_response_pk = Column(
        BigInteger, ForeignKey("appointment_response.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    appointment_response = relationship(
        "AppointmentResponseModel", back_populates="participant_types"
    )
    codings = relationship(
        "AppointmentResponseParticipantTypeCoding",
        back_populates="participant_type",
        cascade="all, delete-orphan",
    )


class AppointmentResponseParticipantTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of AppointmentResponse.participantType.coding (0..*)."""

    __tablename__ = "appointment_response_participant_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_response_participant_type_id = Column(
        BigInteger,
        ForeignKey("appointment_response_participant_type.id"),
        nullable=False,
        index=True,
    )

    participant_type = relationship(
        "AppointmentResponseParticipantType", back_populates="codings"
    )
