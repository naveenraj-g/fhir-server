from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in MedicationAdministrationToken, and the element each reads
# (`code` -> medicationCodeableConcept; `reason-given` -> reasonCode of every entry;
# `reason-not-given` -> statusReason of every entry).
TOKEN_PARAMS = {
    "code": "medicationCodeableConcept",
    "reason-given": "reasonCode",
    "reason-not-given": "statusReason",
}


class MedicationAdministrationToken(Base):
    """Search index for the three CodeableConcept token parameters (`code`, `reason-given`, `reason-not-given`): one row
    per coding of each concept - a token search matches any coding - plus one code-less row for a
    concept with only `text`, so `:text` still finds it. `param` says which search parameter the
    row belongs to (see TOKEN_PARAMS). Derived from MedicationAdministrationModel.content - never read
    to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of three identical ones."""

    __tablename__ = "medication_administration_token"
    __table_args__ = (
        Index("ix_medication_administration_token_param_code", "param", "code"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_pk = Column(
        BigInteger,
        ForeignKey("medication_administration.id"),
        nullable=False,
        index=True,
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    medication_administration = relationship(
        "MedicationAdministrationModel", back_populates="tokens"
    )
