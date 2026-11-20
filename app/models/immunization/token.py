from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in ImmunizationToken, and the Immunization element each
# reads (`target-disease` -> protocolApplied.targetDisease; the others read the
# element of the same name, with `vaccine-code` -> vaccineCode).
TOKEN_PARAMS = {
    "reason-code": "reasonCode",
    "status-reason": "statusReason",
    "target-disease": "protocolApplied.targetDisease",
    "vaccine-code": "vaccineCode",
}


class ImmunizationToken(Base):
    """Search index for the four CodeableConcept token parameters (`reason-code`,
    `status-reason`, `target-disease`, `vaccine-code`): one row per coding of each
    concept — a token search matches any coding of any entry — plus one code-less
    row for a concept with only `text`, so `:text` still finds it. `param` says
    which search parameter the row belongs to (see TOKEN_PARAMS). Derived from
    ImmunizationModel.content — never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of four identical ones."""

    __tablename__ = "immunization_token"
    __table_args__ = (Index("ix_immunization_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(BigInteger, ForeignKey("immunization.id"), nullable=False, index=True)
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    immunization = relationship("ImmunizationModel", back_populates="tokens")
