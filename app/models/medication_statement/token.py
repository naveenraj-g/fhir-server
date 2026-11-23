from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in MedicationStatementToken, and the element each reads
# (`code` -> medicationCodeableConcept; `category` -> category).
TOKEN_PARAMS = {
    "code": "medicationCodeableConcept",
    "category": "category",
}


class MedicationStatementToken(Base):
    """Search index for the two CodeableConcept token parameters (`code`, `category`): one row
    per coding of each concept - a token search matches any coding - plus one code-less row for a
    concept with only `text`, so `:text` still finds it. `param` says which search parameter the
    row belongs to (see TOKEN_PARAMS). Derived from MedicationStatementModel.content - never read
    to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of two identical ones."""

    __tablename__ = "medication_statement_token"
    __table_args__ = (
        Index("ix_medication_statement_token_param_code", "param", "code"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_pk = Column(
        BigInteger, ForeignKey("medication_statement.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    medication_statement = relationship(
        "MedicationStatementModel", back_populates="tokens"
    )
