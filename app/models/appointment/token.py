from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter an AppointmentToken row feeds, and the Appointment
# element it is read from. `appointmentType` is a single CodeableConcept
# (0..1); the others are lists (0..*).
TOKEN_PARAMS = {
    "service-category": "serviceCategory",
    "service-type": "serviceType",
    "specialty": "specialty",
    "appointment-type": "appointmentType",
    "reason-code": "reasonCode",
}


class AppointmentToken(Base):
    """Search index for the five CodeableConcept token parameters
    (`service-category`, `service-type`, `specialty`, `appointment-type`,
    `reason-code`): one row per coding of each concept — a token search
    matches any coding of any entry — plus one code-less row for a concept
    that has only `text`, so `:text` still finds it. `param` says which
    search parameter the row belongs to (see TOKEN_PARAMS). Derived from
    AppointmentModel.content — never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of five identical ones (same design as
    SlotToken)."""

    __tablename__ = "appointment_token"
    __table_args__ = (Index("ix_appointment_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="tokens")
