from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in MedicationRequestToken, and the MedicationRequest element each reads
# (`code` -> medicationCodeableConcept, `intended-performertype` -> performerType; `category`
# reads the element of the same name).
TOKEN_PARAMS = {
    "category": "category",
    "code": "medicationCodeableConcept",
    "intended-performertype": "performerType",
}


class MedicationRequestToken(Base):
    """Search index for the three CodeableConcept token parameters (`category`,
    `code`, `intended-performertype`): one row per coding of each concept — a token search
    matches any coding of any entry — plus one code-less row for a concept with
    only `text`, so `:text` still finds it. `param` says which search parameter
    the row belongs to (see TOKEN_PARAMS). Derived from MedicationRequestModel.content —
    never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of three identical ones."""

    __tablename__ = "medication_request_token"
    __table_args__ = (Index("ix_medication_request_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(
        BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    medication_request = relationship("MedicationRequestModel", back_populates="tokens")
