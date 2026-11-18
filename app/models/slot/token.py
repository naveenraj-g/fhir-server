from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter a SlotToken row feeds, and the Slot element it is read
# from. `appointmentType` is a single CodeableConcept (0..1); the others are
# lists (0..*).
TOKEN_PARAMS = {
    "service-category": "serviceCategory",
    "service-type": "serviceType",
    "specialty": "specialty",
    "appointment-type": "appointmentType",
}


class SlotToken(Base):
    """Search index for the four CodeableConcept token parameters
    (`service-category`, `service-type`, `specialty`, `appointment-type`): one
    row per coding of each concept — a token search matches any coding of any
    entry — plus one code-less row for a concept that has only `text`, so
    `:text` still finds it. `param` says which search parameter the row
    belongs to (see TOKEN_PARAMS). Derived from SlotModel.content — never read
    to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of four identical ones (same design as
    HealthcareServiceToken)."""

    __tablename__ = "slot_token"
    __table_args__ = (Index("ix_slot_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slot_pk = Column(BigInteger, ForeignKey("slot.id"), nullable=False, index=True)
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    slot = relationship("SlotModel", back_populates="tokens")
